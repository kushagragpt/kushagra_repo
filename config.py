"""
Configuration management for the voice agent.
"""

import os
from typing import List
from dataclasses import dataclass


@dataclass
class AgentConfig:
    """Configuration for the voice agent."""
    
    # LiveKit connection settings
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str
    
    # Interruption handling settings
    ignored_words: List[str]
    confidence_threshold: float
    enable_dynamic_updates: bool
    
    # Agent behavior settings
    min_interruption_duration: float
    false_interruption_timeout: float
    resume_false_interruption: bool
    
    @classmethod
    def from_env(cls) -> 'AgentConfig':
        """Load configuration from environment variables."""
        
        # LiveKit settings
        livekit_url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
        livekit_api_key = os.getenv("LIVEKIT_API_KEY", "")
        livekit_api_secret = os.getenv("LIVEKIT_API_SECRET", "")
        
        # Interruption handling
        ignored_words_str = os.getenv("IGNORED_WORDS", "uh,umm,hmm,haan,um,er,ah")
        ignored_words = [word.strip() for word in ignored_words_str.split(",") if word.strip()]
        
        confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
        enable_dynamic_updates = os.getenv("ENABLE_DYNAMIC_UPDATES", "false").lower() == "true"
        
        # Agent behavior
        min_interruption_duration = float(os.getenv("MIN_INTERRUPTION_DURATION", "0.3"))
        false_interruption_timeout = float(os.getenv("FALSE_INTERRUPTION_TIMEOUT", "1.5"))
        resume_false_interruption = os.getenv("RESUME_FALSE_INTERRUPTION", "true").lower() == "true"
        
        return cls(
            livekit_url=livekit_url,
            livekit_api_key=livekit_api_key,
            livekit_api_secret=livekit_api_secret,
            ignored_words=ignored_words,
            confidence_threshold=confidence_threshold,
            enable_dynamic_updates=enable_dynamic_updates,
            min_interruption_duration=min_interruption_duration,
            false_interruption_timeout=false_interruption_timeout,
            resume_false_interruption=resume_false_interruption,
        )
    
    def validate(self) -> bool:
        """Validate the configuration."""
        if not self.livekit_url:
            raise ValueError("LIVEKIT_URL is required")
        if not self.livekit_api_key:
            raise ValueError("LIVEKIT_API_KEY is required")
        if not self.livekit_api_secret:
            raise ValueError("LIVEKIT_API_SECRET is required")
        
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError("CONFIDENCE_THRESHOLD must be between 0.0 and 1.0")
        
        if self.min_interruption_duration < 0:
            raise ValueError("MIN_INTERRUPTION_DURATION must be non-negative")
        
        if self.false_interruption_timeout < 0:
            raise ValueError("FALSE_INTERRUPTION_TIMEOUT must be non-negative")
        
        return True

