"""
LiveKit Voice Agent with Intelligent Interruption Handling
Filters filler words to prevent false interruptions during agent speech.
Supports runtime updates via data messages and multi-language filler detection.
"""

import logging
import os
import asyncio
import json
from typing import Optional
from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    AgentStateChangedEvent,
)
from livekit.plugins import silero, openai, deepgram, cartesia
from livekit import rtc

from interruption_handler import InterruptionHandler, InterruptionConfig, Language

logger = logging.getLogger("voice-agent")
logging.basicConfig(level=logging.INFO)
load_dotenv()


class VoiceAgent(Agent):
    """Voice agent with intelligent interruption handling and runtime controls."""

    def __init__(self, interruption_handler: InterruptionHandler):
        super().__init__(
            instructions=(
                "You are a helpful voice assistant. "
                "Keep your responses concise and natural. "
                "Speak clearly and at a moderate pace."
            )
        )
        self.interruption_handler = interruption_handler
        self._is_speaking = False
        self._agent_session = None

    async def on_enter(self):
        """Called when agent enters the session."""
        logger.info("Agent entered session")
        # Greet the user
        await self.session.generate_reply(
            instructions="Greet the user warmly and ask how you can help them today."
        )

    async def on_exit(self):
        """Called when agent exits the session."""
        logger.info("Agent exited session")

    def handle_control_message(self, data: dict) -> dict:
        """
        Handle runtime control messages for the interruption handler.

        Supported commands:
        - add_word: Add a word to ignored list
        - remove_word: Remove a word from ignored list
        - add_words: Add multiple words
        - remove_words: Remove multiple words
        - add_language: Add a language preset
        - set_threshold: Update confidence threshold
        - get_stats: Get current statistics
        - get_words: Get current ignored words
        - reset: Reset to defaults

        Args:
            data: Command data dictionary

        Returns:
            Response dictionary with status and result
        """
        command = data.get("command")

        try:
            if command == "add_word":
                word = data.get("word", "")
                success = self.interruption_handler.add_ignored_word(word)
                return {"status": "success" if success else "failed", "word": word}

            elif command == "remove_word":
                word = data.get("word", "")
                success = self.interruption_handler.remove_ignored_word(word)
                return {"status": "success" if success else "failed", "word": word}

            elif command == "add_words":
                words = data.get("words", [])
                count = self.interruption_handler.add_ignored_words_bulk(words)
                return {"status": "success", "added_count": count, "total": len(words)}

            elif command == "remove_words":
                words = data.get("words", [])
                count = self.interruption_handler.remove_ignored_words_bulk(words)
                return {"status": "success", "removed_count": count, "total": len(words)}

            elif command == "add_language":
                lang_str = data.get("language", "")
                try:
                    language = Language(lang_str)
                    count = self.interruption_handler.add_language_preset(language)
                    return {"status": "success", "language": lang_str, "added_count": count}
                except ValueError:
                    return {"status": "error", "message": f"Invalid language: {lang_str}"}

            elif command == "set_threshold":
                threshold = data.get("threshold", 0.5)
                success = self.interruption_handler.update_confidence_threshold(float(threshold))
                return {"status": "success" if success else "failed", "threshold": threshold}

            elif command == "get_stats":
                stats = self.interruption_handler.get_stats()
                return {"status": "success", "stats": stats}

            elif command == "get_words":
                words = list(self.interruption_handler.get_ignored_words())
                by_lang = self.interruption_handler.get_ignored_words_by_language()
                return {
                    "status": "success",
                    "words": sorted(words),
                    "by_language": {k: sorted(v) for k, v in by_lang.items()}
                }

            elif command == "reset":
                lang_str = data.get("language")
                language = Language(lang_str) if lang_str else None
                self.interruption_handler.reset_to_defaults(language)
                return {"status": "success", "reset_to": lang_str or "current"}

            else:
                return {"status": "error", "message": f"Unknown command: {command}"}

        except Exception as e:
            logger.error(f"Error handling control message: {e}")
            return {"status": "error", "message": str(e)}


def prewarm(proc: JobProcess):
    """Prewarm function to load models before handling requests."""
    logger.info("Prewarming models...")
    proc.userdata["vad"] = silero.VAD.load()
    logger.info("VAD model loaded")


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the voice agent."""

    # Set up logging context
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    logger.info(f"Starting agent for room: {ctx.room.name}")

    # Check if we should use language presets or custom word list
    use_language_presets = os.getenv("USE_LANGUAGE_PRESETS", "true").lower() == "true"

    if use_language_presets:
        # Use language-based configuration
        languages_str = os.getenv("LANGUAGES", "mixed")
        language_list = []

        for lang_str in languages_str.split(","):
            lang_str = lang_str.strip().lower()
            if lang_str == "en" or lang_str == "english":
                language_list.append(Language.ENGLISH)
            elif lang_str == "hi" or lang_str == "hindi":
                language_list.append(Language.HINDI)
            elif lang_str == "mixed":
                language_list.append(Language.MIXED)

        if not language_list:
            language_list = [Language.MIXED]  # Default to mixed

        confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))

        # Get any additional custom words
        additional_words_str = os.getenv("ADDITIONAL_IGNORED_WORDS", "")
        additional_words = [w.strip() for w in additional_words_str.split(",") if w.strip()]

        config = InterruptionConfig.from_languages(
            languages=language_list,
            confidence_threshold=confidence_threshold,
            enable_dynamic_updates=True,
            additional_words=additional_words if additional_words else None
        )

        logger.info(f"Using language presets: {[lang.value for lang in language_list]}")
        if additional_words:
            logger.info(f"Additional custom words: {additional_words}")
    else:
        # Use custom word list (legacy mode)
        ignored_words_str = os.getenv("IGNORED_WORDS", "uh,umm,hmm,haan,um,er,ah")
        ignored_words = [word.strip() for word in ignored_words_str.split(",")]
        confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))

        config = InterruptionConfig.from_word_list(
            words=ignored_words,
            confidence_threshold=confidence_threshold,
            enable_dynamic_updates=True
        )

        logger.info(f"Using custom word list with {len(ignored_words)} words")

    interruption_handler = InterruptionHandler(config)
    logger.info(f"Interruption handler initialized with {len(interruption_handler.get_ignored_words())} ignored words")

    # Create the agent
    agent = VoiceAgent(interruption_handler)

    # Connect to the room first
    await ctx.connect()

    # Create agent session with STT-LLM-TTS pipeline
    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(model="nova-3"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=cartesia.TTS(),
        # Enable false interruption handling as a fallback
        resume_false_interruption=True,
        false_interruption_timeout=1.5,
        # Minimum interruption settings
        min_interruption_duration=0.3,
        min_interruption_words=0,  # We handle word filtering ourselves
    )

    agent._agent_session = session

    # Track agent speaking state
    @session.on("agent_state_changed")
    def on_agent_state_changed(ev: AgentStateChangedEvent):
        if ev.new_state == "speaking":
            agent._is_speaking = True
            logger.info("Agent started speaking")
        elif ev.new_state in ["listening", "thinking", "idle"]:
            was_speaking = agent._is_speaking
            agent._is_speaking = False
            if was_speaking:
                logger.info(f"Agent stopped speaking, now: {ev.new_state}")

    # Monitor VAD events to detect potential interruptions early
    vad_buffer = []
    vad_start_time = None

    @session.on("user_started_speaking")
    def on_user_started_speaking(ev):
        """Detect when user starts speaking."""
        nonlocal vad_start_time
        vad_start_time = asyncio.get_event_loop().time()

        if agent._is_speaking:
            logger.debug("User started speaking while agent is speaking (potential interruption)")

    @session.on("user_stopped_speaking")
    def on_user_stopped_speaking(ev):
        """Detect when user stops speaking."""
        nonlocal vad_start_time
        if vad_start_time:
            duration = asyncio.get_event_loop().time() - vad_start_time
            logger.debug(f"User speech duration: {duration:.2f}s")
            vad_start_time = None

    # Hook into transcription events to filter filler words
    @session.on("user_transcript")
    def on_user_transcript(ev):
        """Handle interim and final transcripts."""
        # Get the transcript text
        text = ev.text if hasattr(ev, 'text') else ""
        confidence = ev.confidence if hasattr(ev, 'confidence') else None
        is_final = ev.is_final if hasattr(ev, 'is_final') else False

        if not text:
            return

        logger.debug(f"Transcript ({'final' if is_final else 'interim'}): '{text}' (confidence: {confidence})")

        # Only filter during agent speech (potential interruption)
        if agent._is_speaking and is_final:
            should_ignore = interruption_handler.should_ignore_speech(text, confidence)

            if should_ignore:
                logger.info(f"🔇 Filtered filler interruption: '{text}' (confidence: {confidence})")
                # This is a filler - don't let it interrupt the agent
                # The agent will continue speaking
                return
            else:
                logger.info(f"✅ Valid interruption detected: '{text}'")

    # Handle data messages for runtime control
    @ctx.room.on("data_received")
    def on_data_received(data: rtc.DataPacket):
        """Handle control messages sent via data channel."""
        try:
            # Decode the data message
            message_str = data.data.decode('utf-8')
            message = json.loads(message_str)

            logger.info(f"📨 Received control message: {message.get('command')}")

            # Process the control command
            response = agent.handle_control_message(message)

            # Send response back via data channel
            response_str = json.dumps(response)
            ctx.room.local_participant.publish_data(
                response_str.encode('utf-8'),
                reliable=True
            )

            logger.info(f"📤 Sent response: {response.get('status')}")

        except json.JSONDecodeError:
            logger.error("Failed to decode control message as JSON")
        except Exception as e:
            logger.error(f"Error handling data message: {e}")

    # Start the session
    await session.start(
        agent=agent,
        room=ctx.room,
    )

    logger.info("Agent session started successfully")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))

