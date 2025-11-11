"""
Interruption Handler for LiveKit Voice Agent
Filters out filler words and low-confidence speech to prevent false interruptions.
Supports multi-language filler detection with language-specific word sets.
"""

import logging
import re
from typing import List, Set, Optional, Dict
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Language(Enum):
    """Supported languages for filler detection."""
    ENGLISH = "en"
    HINDI = "hi"
    MIXED = "mixed"  # For mixed language scenarios


# Predefined filler word sets for different languages
LANGUAGE_FILLERS: Dict[Language, Set[str]] = {
    Language.ENGLISH: {
        "uh", "um", "umm", "er", "ah", "eh", "hmm", "hm",
        "like", "you know", "i mean", "sort of", "kind of",
        "basically", "actually", "literally", "well", "so",
        "yeah", "yep", "yup", "nah", "nope", "mhm", "uh-huh",
        "mm-hmm", "uh-uh", "mm-mm"
    },
    Language.HINDI: {
        "haan", "han", "hmm", "achha", "accha", "theek", "thik",
        "matlab", "yaani", "kya", "toh", "to", "bas", "arre",
        "arrey", "arey", "haa", "naa", "na", "ji", "hnji",
        "acha", "aha", "oho", "uff", "arre bhai", "yaar"
    }
}

# Mixed language includes both English and Hindi fillers
LANGUAGE_FILLERS[Language.MIXED] = (
    LANGUAGE_FILLERS[Language.ENGLISH] | LANGUAGE_FILLERS[Language.HINDI]
)


@dataclass
class InterruptionConfig:
    """Configuration for interruption detection with multi-language support."""
    ignored_words: Set[str]
    confidence_threshold: float = 0.5
    enable_dynamic_updates: bool = False
    languages: List[Language] = field(default_factory=lambda: [Language.MIXED])
    use_language_presets: bool = True  # Whether to use predefined language filler sets

    @classmethod
    def from_word_list(cls, words: List[str], confidence_threshold: float = 0.5,
                       enable_dynamic_updates: bool = False) -> 'InterruptionConfig':
        """Create config from a list of words to ignore."""
        # Normalize words: lowercase and strip whitespace
        normalized_words = {word.lower().strip() for word in words if word.strip()}
        return cls(
            ignored_words=normalized_words,
            confidence_threshold=confidence_threshold,
            enable_dynamic_updates=enable_dynamic_updates,
            use_language_presets=False  # Custom word list, don't use presets
        )

    @classmethod
    def from_languages(cls, languages: List[Language], confidence_threshold: float = 0.5,
                      enable_dynamic_updates: bool = False,
                      additional_words: Optional[List[str]] = None) -> 'InterruptionConfig':
        """
        Create config from language presets.

        Args:
            languages: List of languages to support (e.g., [Language.ENGLISH, Language.HINDI])
            confidence_threshold: Minimum confidence for valid speech
            enable_dynamic_updates: Allow runtime updates
            additional_words: Additional custom words to add to the preset
        """
        # Combine filler words from all specified languages
        ignored_words = set()
        for lang in languages:
            if lang in LANGUAGE_FILLERS:
                ignored_words.update(LANGUAGE_FILLERS[lang])

        # Add any additional custom words
        if additional_words:
            ignored_words.update(word.lower().strip() for word in additional_words if word.strip())

        return cls(
            ignored_words=ignored_words,
            confidence_threshold=confidence_threshold,
            enable_dynamic_updates=enable_dynamic_updates,
            languages=languages,
            use_language_presets=True
        )


class InterruptionHandler:
    """
    Handles interruption detection for LiveKit voice agents.

    This class filters out filler words and low-confidence speech segments
    to prevent false interruptions during agent speech.
    Supports multi-language filler detection and runtime updates.
    """

    def __init__(self, config: InterruptionConfig):
        """
        Initialize the interruption handler.

        Args:
            config: Configuration for interruption detection
        """
        self.config = config
        self._ignored_words = config.ignored_words.copy()
        self._confidence_threshold = config.confidence_threshold
        self._enable_dynamic_updates = config.enable_dynamic_updates
        self._languages = config.languages
        self._use_language_presets = config.use_language_presets

        # Track statistics for runtime monitoring
        self._stats = {
            "total_speech_events": 0,
            "ignored_filler_count": 0,
            "ignored_low_confidence_count": 0,
            "valid_interruptions": 0,
            "dynamic_updates_count": 0
        }

        logger.info(f"InterruptionHandler initialized with {len(self._ignored_words)} ignored words")
        if self._use_language_presets:
            logger.info(f"Languages: {[lang.value for lang in self._languages]}")
        logger.debug(f"Ignored words: {sorted(self._ignored_words)}")
        logger.info(f"Confidence threshold: {self._confidence_threshold}")
        logger.info(f"Dynamic updates: {'enabled' if self._enable_dynamic_updates else 'disabled'}")
    
    def should_ignore_speech(self, text: str, confidence: Optional[float] = None) -> bool:
        """
        Determine if speech should be ignored (not treated as interruption).

        Args:
            text: The transcribed text from user speech
            confidence: Optional confidence score from ASR (0.0 to 1.0)

        Returns:
            True if speech should be ignored, False if it's a valid interruption
        """
        self._stats["total_speech_events"] += 1

        # Check confidence threshold first
        if confidence is not None and confidence < self._confidence_threshold:
            self._stats["ignored_low_confidence_count"] += 1
            logger.debug(f"Ignoring low-confidence speech: '{text}' (confidence: {confidence:.2f})")
            return True

        # Normalize the input text
        normalized_text = self._normalize_text(text)

        # Check if the entire text is empty after normalization
        if not normalized_text:
            logger.debug(f"Ignoring empty text after normalization: '{text}'")
            return True

        # First check if the entire phrase is a filler phrase (for multi-word fillers)
        if normalized_text in self._ignored_words:
            self._stats["ignored_filler_count"] += 1
            logger.debug(f"Ignoring filler phrase: '{text}'")
            return True

        # Split into words and check if all are filler words
        words = normalized_text.split()

        # Check each word individually
        non_filler_words = []
        for word in words:
            if word not in self._ignored_words:
                non_filler_words.append(word)

        # If all words are fillers, ignore this speech
        if not non_filler_words:
            self._stats["ignored_filler_count"] += 1
            logger.debug(f"Ignoring filler-only speech: '{text}' -> words: {words}")
            return True

        # This is valid speech with meaningful content
        self._stats["valid_interruptions"] += 1
        logger.debug(f"Valid interruption detected: '{text}' -> meaningful words: {non_filler_words}")
        return False
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison.

        Args:
            text: Raw text to normalize

        Returns:
            Normalized text (lowercase, no punctuation, trimmed)
        """
        # Convert to lowercase
        text = text.lower()

        # Remove punctuation and special characters, keep only alphanumeric and spaces
        # Keep spaces to preserve multi-word phrases
        text = re.sub(r'[^a-z0-9\s]', ' ', text)

        # Normalize whitespace (collapse multiple spaces into one)
        text = ' '.join(text.split())

        return text
    
    def add_ignored_word(self, word: str) -> bool:
        """
        Dynamically add a word to the ignored list.

        Args:
            word: Word to add to ignored list

        Returns:
            True if word was added, False otherwise
        """
        if not self._enable_dynamic_updates:
            logger.warning("Dynamic updates are disabled. Enable them in config to add words at runtime.")
            return False

        normalized_word = word.lower().strip()
        if normalized_word and normalized_word not in self._ignored_words:
            self._ignored_words.add(normalized_word)
            self._stats["dynamic_updates_count"] += 1
            logger.info(f"✅ Added '{normalized_word}' to ignored words list")
            return True
        elif normalized_word in self._ignored_words:
            logger.debug(f"Word '{normalized_word}' already in ignored list")
            return False
        return False

    def remove_ignored_word(self, word: str) -> bool:
        """
        Dynamically remove a word from the ignored list.

        Args:
            word: Word to remove from ignored list

        Returns:
            True if word was removed, False otherwise
        """
        if not self._enable_dynamic_updates:
            logger.warning("Dynamic updates are disabled. Enable them in config to remove words at runtime.")
            return False

        normalized_word = word.lower().strip()
        if normalized_word in self._ignored_words:
            self._ignored_words.remove(normalized_word)
            self._stats["dynamic_updates_count"] += 1
            logger.info(f"✅ Removed '{normalized_word}' from ignored words list")
            return True
        else:
            logger.debug(f"Word '{normalized_word}' not in ignored list")
            return False

    def add_ignored_words_bulk(self, words: List[str]) -> int:
        """
        Add multiple words to the ignored list at once.

        Args:
            words: List of words to add

        Returns:
            Number of words successfully added
        """
        if not self._enable_dynamic_updates:
            logger.warning("Dynamic updates are disabled.")
            return 0

        added_count = 0
        for word in words:
            if self.add_ignored_word(word):
                added_count += 1

        logger.info(f"Bulk add: {added_count}/{len(words)} words added")
        return added_count

    def remove_ignored_words_bulk(self, words: List[str]) -> int:
        """
        Remove multiple words from the ignored list at once.

        Args:
            words: List of words to remove

        Returns:
            Number of words successfully removed
        """
        if not self._enable_dynamic_updates:
            logger.warning("Dynamic updates are disabled.")
            return 0

        removed_count = 0
        for word in words:
            if self.remove_ignored_word(word):
                removed_count += 1

        logger.info(f"Bulk remove: {removed_count}/{len(words)} words removed")
        return removed_count

    def add_language_preset(self, language: Language) -> int:
        """
        Add all filler words from a language preset.

        Args:
            language: Language preset to add

        Returns:
            Number of new words added
        """
        if not self._enable_dynamic_updates:
            logger.warning("Dynamic updates are disabled.")
            return 0

        if language not in LANGUAGE_FILLERS:
            logger.warning(f"Language {language.value} not found in presets")
            return 0

        words_to_add = LANGUAGE_FILLERS[language]
        initial_count = len(self._ignored_words)
        self._ignored_words.update(words_to_add)
        added_count = len(self._ignored_words) - initial_count

        if language not in self._languages:
            self._languages.append(language)

        self._stats["dynamic_updates_count"] += 1
        logger.info(f"✅ Added {added_count} words from {language.value} preset")
        return added_count
    
    def get_ignored_words(self) -> Set[str]:
        """Get the current set of ignored words."""
        return self._ignored_words.copy()

    def get_ignored_words_by_language(self) -> Dict[str, Set[str]]:
        """
        Get ignored words categorized by language.

        Returns:
            Dictionary mapping language names to their filler words
        """
        result = {}
        for lang in self._languages:
            if lang in LANGUAGE_FILLERS:
                # Only include words that are currently in the ignored list
                lang_words = LANGUAGE_FILLERS[lang] & self._ignored_words
                if lang_words:
                    result[lang.value] = lang_words

        # Also include custom words (not in any preset)
        all_preset_words = set()
        for lang_fillers in LANGUAGE_FILLERS.values():
            all_preset_words.update(lang_fillers)

        custom_words = self._ignored_words - all_preset_words
        if custom_words:
            result["custom"] = custom_words

        return result

    def update_confidence_threshold(self, threshold: float) -> bool:
        """
        Update the confidence threshold.

        Args:
            threshold: New confidence threshold (0.0 to 1.0)

        Returns:
            True if updated successfully, False otherwise
        """
        if not self._enable_dynamic_updates:
            logger.warning("Dynamic updates are disabled.")
            return False

        if not 0.0 <= threshold <= 1.0:
            logger.error("Confidence threshold must be between 0.0 and 1.0")
            return False

        old_threshold = self._confidence_threshold
        self._confidence_threshold = threshold
        self._stats["dynamic_updates_count"] += 1
        logger.info(f"✅ Updated confidence threshold from {old_threshold:.2f} to {threshold:.2f}")
        return True

    def reset_to_defaults(self, language: Optional[Language] = None) -> None:
        """
        Reset ignored words to default preset for a language.

        Args:
            language: Language to reset to. If None, uses current languages.
        """
        if not self._enable_dynamic_updates:
            logger.warning("Dynamic updates are disabled.")
            return

        if language:
            if language in LANGUAGE_FILLERS:
                self._ignored_words = LANGUAGE_FILLERS[language].copy()
                self._languages = [language]
                logger.info(f"✅ Reset to {language.value} defaults")
        else:
            # Reset to current languages
            self._ignored_words = set()
            for lang in self._languages:
                if lang in LANGUAGE_FILLERS:
                    self._ignored_words.update(LANGUAGE_FILLERS[lang])
            logger.info(f"✅ Reset to defaults for languages: {[l.value for l in self._languages]}")

        self._stats["dynamic_updates_count"] += 1

    def get_stats(self) -> dict:
        """Get current handler statistics and configuration."""
        return {
            "ignored_words_count": len(self._ignored_words),
            "confidence_threshold": self._confidence_threshold,
            "dynamic_updates_enabled": self._enable_dynamic_updates,
            "languages": [lang.value for lang in self._languages],
            "use_language_presets": self._use_language_presets,
            "ignored_words": sorted(self._ignored_words),
            "statistics": self._stats.copy()
        }

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self._stats = {
            "total_speech_events": 0,
            "ignored_filler_count": 0,
            "ignored_low_confidence_count": 0,
            "valid_interruptions": 0,
            "dynamic_updates_count": 0
        }
        logger.info("Statistics reset")

