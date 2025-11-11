# Runtime Control API Reference

This document provides a complete reference for the runtime control API of the interruption handler.

## Table of Contents

- [Overview](#overview)
- [Python API](#python-api)
- [LiveKit Data Channel API](#livekit-data-channel-api)
- [Configuration](#configuration)
- [Examples](#examples)

---

## Overview

The interruption handler supports dynamic updates during runtime without requiring agent restart. This enables:

- Adding/removing ignored words on-the-fly
- Switching between language presets
- Adjusting confidence thresholds
- Monitoring statistics in real-time

**Requirements:**
- `enable_dynamic_updates=True` in configuration
- For LiveKit control: Active LiveKit room connection

---

## Python API

### Word Management

#### `add_ignored_word(word: str) -> bool`

Add a single word to the ignored list.

```python
success = handler.add_ignored_word("okay")
# Returns: True if added, False if already exists or updates disabled
```

#### `remove_ignored_word(word: str) -> bool`

Remove a single word from the ignored list.

```python
success = handler.remove_ignored_word("okay")
# Returns: True if removed, False if not found or updates disabled
```

#### `add_ignored_words_bulk(words: List[str]) -> int`

Add multiple words at once.

```python
count = handler.add_ignored_words_bulk(["okay", "right", "sure"])
# Returns: Number of words successfully added
```

#### `remove_ignored_words_bulk(words: List[str]) -> int`

Remove multiple words at once.

```python
count = handler.remove_ignored_words_bulk(["okay", "right"])
# Returns: Number of words successfully removed
```

### Language Preset Management

#### `add_language_preset(language: Language) -> int`

Add all filler words from a language preset.

```python
from interruption_handler import Language

count = handler.add_language_preset(Language.HINDI)
# Returns: Number of new words added
# Available: Language.ENGLISH, Language.HINDI, Language.MIXED
```

#### `reset_to_defaults(language: Optional[Language] = None) -> None`

Reset ignored words to default preset.

```python
# Reset to specific language
handler.reset_to_defaults(Language.ENGLISH)

# Reset to current configured languages
handler.reset_to_defaults()
```

### Configuration Updates

#### `update_confidence_threshold(threshold: float) -> bool`

Update the confidence threshold for speech filtering.

```python
success = handler.update_confidence_threshold(0.3)
# Returns: True if updated, False if invalid or updates disabled
# Valid range: 0.0 to 1.0
```

### Information Retrieval

#### `get_ignored_words() -> Set[str]`

Get the current set of all ignored words.

```python
words = handler.get_ignored_words()
# Returns: Set of ignored words
```

#### `get_ignored_words_by_language() -> Dict[str, Set[str]]`

Get ignored words categorized by language.

```python
words_by_lang = handler.get_ignored_words_by_language()
# Returns: {"en": {...}, "hi": {...}, "custom": {...}}
```

#### `get_stats() -> dict`

Get comprehensive statistics and configuration.

```python
stats = handler.get_stats()
# Returns:
# {
#     "ignored_words_count": 54,
#     "confidence_threshold": 0.5,
#     "dynamic_updates_enabled": True,
#     "languages": ["mixed"],
#     "use_language_presets": True,
#     "ignored_words": [...],
#     "statistics": {
#         "total_speech_events": 100,
#         "ignored_filler_count": 45,
#         "ignored_low_confidence_count": 10,
#         "valid_interruptions": 45,
#         "dynamic_updates_count": 5
#     }
# }
```

#### `reset_stats() -> None`

Reset statistics counters to zero.

```python
handler.reset_stats()
```

---

## LiveKit Data Channel API

Send JSON messages via LiveKit's data channel to control the agent at runtime.

### Message Format

All messages follow this structure:

```json
{
  "command": "command_name",
  "param1": "value1",
  "param2": "value2"
}
```

### Available Commands

#### Add Word

```json
{
  "command": "add_word",
  "word": "okay"
}
```

**Response:**
```json
{
  "status": "success",
  "word": "okay"
}
```

#### Remove Word

```json
{
  "command": "remove_word",
  "word": "okay"
}
```

**Response:**
```json
{
  "status": "success",
  "word": "okay"
}
```

#### Add Multiple Words

```json
{
  "command": "add_words",
  "words": ["okay", "right", "sure"]
}
```

**Response:**
```json
{
  "status": "success",
  "added_count": 3,
  "total": 3
}
```

#### Remove Multiple Words

```json
{
  "command": "remove_words",
  "words": ["okay", "right"]
}
```

**Response:**
```json
{
  "status": "success",
  "removed_count": 2,
  "total": 2
}
```

#### Add Language Preset

```json
{
  "command": "add_language",
  "language": "hi"
}
```

**Language codes:** `en` (English), `hi` (Hindi), `mixed` (Both)

**Response:**
```json
{
  "status": "success",
  "language": "hi",
  "added_count": 27
}
```

#### Set Confidence Threshold

```json
{
  "command": "set_threshold",
  "threshold": 0.3
}
```

**Response:**
```json
{
  "status": "success",
  "threshold": 0.3
}
```

#### Get Statistics

```json
{
  "command": "get_stats"
}
```

**Response:**
```json
{
  "status": "success",
  "stats": {
    "ignored_words_count": 54,
    "confidence_threshold": 0.5,
    ...
  }
}
```

#### Get Words

```json
{
  "command": "get_words"
}
```

**Response:**
```json
{
  "status": "success",
  "words": ["uh", "umm", "haan", ...],
  "by_language": {
    "en": ["uh", "umm", ...],
    "hi": ["haan", "achha", ...],
    "custom": ["okay", ...]
  }
}
```

#### Reset to Defaults

```json
{
  "command": "reset",
  "language": "en"
}
```

**Response:**
```json
{
  "status": "success",
  "reset_to": "en"
}
```

### Error Responses

```json
{
  "status": "error",
  "message": "Error description"
}
```

---

## Configuration

### Environment Variables

```env
# Enable runtime updates
ENABLE_DYNAMIC_UPDATES=true

# Use language presets
USE_LANGUAGE_PRESETS=true
LANGUAGES=mixed                    # en, hi, mixed, or comma-separated

# Additional custom words
ADDITIONAL_IGNORED_WORDS=okay,right

# Confidence threshold
CONFIDENCE_THRESHOLD=0.5
```

### Code Configuration

```python
from interruption_handler import InterruptionConfig, Language

# With language presets
config = InterruptionConfig.from_languages(
    languages=[Language.MIXED],
    confidence_threshold=0.5,
    enable_dynamic_updates=True,
    additional_words=["okay", "right"]
)

# With custom word list
config = InterruptionConfig.from_word_list(
    words=["uh", "umm", "haan"],
    confidence_threshold=0.5,
    enable_dynamic_updates=True
)
```

---

## Examples

### Example 1: Add Custom Words During Conversation

```python
# User says "okay" frequently as a filler
handler.add_ignored_word("okay")

# Now "okay" will be ignored as a filler
handler.should_ignore_speech("okay")  # Returns True
```

### Example 2: Switch Language Context

```python
# Start with English
config = InterruptionConfig.from_languages([Language.ENGLISH])
handler = InterruptionHandler(config)

# User switches to Hindi
handler.add_language_preset(Language.HINDI)

# Now both English and Hindi fillers are ignored
```

### Example 3: Adjust Sensitivity

```python
# Too many false positives? Lower the threshold
handler.update_confidence_threshold(0.3)

# Too many false negatives? Raise the threshold
handler.update_confidence_threshold(0.7)
```

### Example 4: Monitor Performance

```python
# Get statistics
stats = handler.get_stats()

print(f"Total events: {stats['statistics']['total_speech_events']}")
print(f"Fillers filtered: {stats['statistics']['ignored_filler_count']}")
print(f"Valid interruptions: {stats['statistics']['valid_interruptions']}")

# Calculate filter rate
filter_rate = stats['statistics']['ignored_filler_count'] / stats['statistics']['total_speech_events']
print(f"Filter rate: {filter_rate:.1%}")
```

### Example 5: LiveKit Integration

```javascript
// Client-side JavaScript
const room = new Room();

// Add a word
room.localParticipant.publishData(
  JSON.stringify({
    command: "add_word",
    word: "okay"
  }),
  { reliable: true }
);

// Listen for response
room.on('dataReceived', (data) => {
  const response = JSON.parse(new TextDecoder().decode(data));
  console.log('Response:', response);
});
```

---

## Best Practices

1. **Start Conservative**: Begin with language presets, add custom words as needed
2. **Monitor Statistics**: Use `get_stats()` to track performance
3. **Test Changes**: Verify behavior after runtime updates
4. **Document Custom Words**: Keep track of why custom words were added
5. **Reset When Needed**: Use `reset_to_defaults()` to start fresh

---

## Troubleshooting

**Q: Updates not working?**
- Ensure `enable_dynamic_updates=True` in configuration

**Q: Word not being ignored?**
- Check spelling and case (words are normalized to lowercase)
- Verify word is in the list: `handler.get_ignored_words()`

**Q: Too many/few fillers filtered?**
- Adjust `confidence_threshold` (lower = more filtering, higher = less filtering)
- Review statistics to understand current behavior

**Q: LiveKit messages not working?**
- Verify room connection is active
- Check message format is valid JSON
- Look for error responses in data channel

