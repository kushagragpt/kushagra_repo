"""
Demo script for runtime control of the interruption handler.
Shows how to dynamically update ignored words and settings during runtime.
"""

from interruption_handler import InterruptionHandler, InterruptionConfig, Language
import time


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_stats(handler):
    """Print current handler statistics."""
    stats = handler.get_stats()
    print(f"\n📊 Current Statistics:")
    print(f"  - Total ignored words: {stats['ignored_words_count']}")
    print(f"  - Confidence threshold: {stats['confidence_threshold']}")
    print(f"  - Languages: {', '.join(stats['languages'])}")
    print(f"  - Dynamic updates enabled: {stats['dynamic_updates_enabled']}")
    print(f"\n  Speech Events:")
    print(f"  - Total: {stats['statistics']['total_speech_events']}")
    print(f"  - Ignored (fillers): {stats['statistics']['ignored_filler_count']}")
    print(f"  - Ignored (low confidence): {stats['statistics']['ignored_low_confidence_count']}")
    print(f"  - Valid interruptions: {stats['statistics']['valid_interruptions']}")
    print(f"  - Dynamic updates made: {stats['statistics']['dynamic_updates_count']}")


def demo_basic_usage():
    """Demo basic interruption handling."""
    print_section("1. Basic Interruption Handling")
    
    config = InterruptionConfig.from_languages([Language.MIXED], enable_dynamic_updates=True)
    handler = InterruptionHandler(config)
    
    test_cases = [
        ("uh", "Filler word"),
        ("hello", "Real word"),
        ("umm wait", "Mixed"),
        ("haan achha", "Hindi fillers"),
        ("you know", "Multi-word filler"),
    ]
    
    print("\n🧪 Testing speech detection:")
    for text, description in test_cases:
        ignored = handler.should_ignore_speech(text)
        status = "🔇 IGNORED" if ignored else "✅ VALID"
        print(f"  {status}: '{text}' ({description})")
    
    print_stats(handler)


def demo_runtime_word_updates():
    """Demo adding and removing words at runtime."""
    print_section("2. Runtime Word Updates")
    
    config = InterruptionConfig.from_word_list(["uh", "umm"], enable_dynamic_updates=True)
    handler = InterruptionHandler(config)
    
    print("\n📝 Initial state:")
    print(f"  Ignored words: {sorted(handler.get_ignored_words())}")
    
    # Test before adding
    print("\n🧪 Before adding 'okay':")
    ignored = handler.should_ignore_speech("okay")
    print(f"  'okay' is {'ignored' if ignored else 'NOT ignored'}")
    
    # Add word
    print("\n➕ Adding 'okay' to ignored list...")
    handler.add_ignored_word("okay")
    print(f"  Ignored words: {sorted(handler.get_ignored_words())}")
    
    # Test after adding
    print("\n🧪 After adding 'okay':")
    ignored = handler.should_ignore_speech("okay")
    print(f"  'okay' is {'ignored' if ignored else 'NOT ignored'}")
    
    # Remove word
    print("\n➖ Removing 'okay' from ignored list...")
    handler.remove_ignored_word("okay")
    print(f"  Ignored words: {sorted(handler.get_ignored_words())}")
    
    # Test after removing
    print("\n🧪 After removing 'okay':")
    ignored = handler.should_ignore_speech("okay")
    print(f"  'okay' is {'ignored' if ignored else 'NOT ignored'}")


def demo_bulk_operations():
    """Demo bulk add/remove operations."""
    print_section("3. Bulk Operations")
    
    config = InterruptionConfig.from_word_list(["uh"], enable_dynamic_updates=True)
    handler = InterruptionHandler(config)
    
    print("\n📝 Initial state:")
    print(f"  Ignored words: {sorted(handler.get_ignored_words())}")
    
    # Bulk add
    words_to_add = ["okay", "right", "sure", "gotcha", "alright"]
    print(f"\n➕ Adding {len(words_to_add)} words in bulk: {words_to_add}")
    count = handler.add_ignored_words_bulk(words_to_add)
    print(f"  ✅ Added {count} words")
    print(f"  Ignored words: {sorted(handler.get_ignored_words())}")
    
    # Bulk remove
    words_to_remove = ["okay", "right"]
    print(f"\n➖ Removing {len(words_to_remove)} words in bulk: {words_to_remove}")
    count = handler.remove_ignored_words_bulk(words_to_remove)
    print(f"  ✅ Removed {count} words")
    print(f"  Ignored words: {sorted(handler.get_ignored_words())}")


def demo_language_presets():
    """Demo adding language presets at runtime."""
    print_section("4. Language Preset Management")
    
    config = InterruptionConfig.from_word_list(["uh", "umm"], enable_dynamic_updates=True)
    handler = InterruptionHandler(config)
    
    print("\n📝 Initial state (custom words only):")
    print(f"  Total ignored words: {len(handler.get_ignored_words())}")
    
    # Test Hindi filler before adding preset
    print("\n🧪 Before adding Hindi preset:")
    ignored = handler.should_ignore_speech("haan")
    print(f"  'haan' (Hindi filler) is {'ignored' if ignored else 'NOT ignored'}")
    
    # Add Hindi preset
    print("\n🌐 Adding Hindi language preset...")
    count = handler.add_language_preset(Language.HINDI)
    print(f"  ✅ Added {count} Hindi filler words")
    print(f"  Total ignored words: {len(handler.get_ignored_words())}")
    
    # Test Hindi filler after adding preset
    print("\n🧪 After adding Hindi preset:")
    ignored = handler.should_ignore_speech("haan")
    print(f"  'haan' (Hindi filler) is {'ignored' if ignored else 'NOT ignored'}")
    
    # Add English preset
    print("\n🌐 Adding English language preset...")
    count = handler.add_language_preset(Language.ENGLISH)
    print(f"  ✅ Added {count} English filler words")
    print(f"  Total ignored words: {len(handler.get_ignored_words())}")


def demo_multi_language():
    """Demo multi-language filler detection."""
    print_section("5. Multi-Language Filler Detection")
    
    # English only
    print("\n🇬🇧 English-only configuration:")
    config_en = InterruptionConfig.from_languages([Language.ENGLISH])
    handler_en = InterruptionHandler(config_en)
    
    test_cases = [
        ("uh", "English filler"),
        ("you know", "English phrase filler"),
        ("haan", "Hindi filler"),
    ]
    
    for text, description in test_cases:
        ignored = handler_en.should_ignore_speech(text)
        status = "🔇" if ignored else "✅"
        print(f"  {status} '{text}' ({description})")
    
    # Hindi only
    print("\n🇮🇳 Hindi-only configuration:")
    config_hi = InterruptionConfig.from_languages([Language.HINDI])
    handler_hi = InterruptionHandler(config_hi)
    
    for text, description in test_cases:
        ignored = handler_hi.should_ignore_speech(text)
        status = "🔇" if ignored else "✅"
        print(f"  {status} '{text}' ({description})")
    
    # Mixed
    print("\n🌍 Mixed language configuration:")
    config_mixed = InterruptionConfig.from_languages([Language.MIXED])
    handler_mixed = InterruptionHandler(config_mixed)
    
    for text, description in test_cases:
        ignored = handler_mixed.should_ignore_speech(text)
        status = "🔇" if ignored else "✅"
        print(f"  {status} '{text}' ({description})")
    
    # Show words by language
    print("\n📚 Words categorized by language:")
    config_both = InterruptionConfig.from_languages([Language.ENGLISH, Language.HINDI])
    handler_both = InterruptionHandler(config_both)
    words_by_lang = handler_both.get_ignored_words_by_language()
    
    for lang, words in words_by_lang.items():
        print(f"  {lang}: {len(words)} words")
        print(f"    Sample: {', '.join(sorted(list(words))[:5])}")


def demo_confidence_threshold():
    """Demo confidence threshold updates."""
    print_section("6. Confidence Threshold Management")
    
    config = InterruptionConfig.from_word_list(
        ["uh"], 
        confidence_threshold=0.5,
        enable_dynamic_updates=True
    )
    handler = InterruptionHandler(config)
    
    print("\n📝 Initial threshold: 0.5")
    
    test_confidences = [0.3, 0.4, 0.5, 0.6, 0.7]
    
    print("\n🧪 Testing with threshold 0.5:")
    for conf in test_confidences:
        ignored = handler.should_ignore_speech("hello", confidence=conf)
        status = "🔇 IGNORED" if ignored else "✅ VALID"
        print(f"  {status}: confidence {conf}")
    
    # Update threshold
    print("\n🔧 Updating threshold to 0.3...")
    handler.update_confidence_threshold(0.3)
    
    print("\n🧪 Testing with threshold 0.3:")
    for conf in test_confidences:
        ignored = handler.should_ignore_speech("hello", confidence=conf)
        status = "🔇 IGNORED" if ignored else "✅ VALID"
        print(f"  {status}: confidence {conf}")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("  🎯 Runtime Control Demo for Interruption Handler")
    print("="*70)
    
    demo_basic_usage()
    demo_runtime_word_updates()
    demo_bulk_operations()
    demo_language_presets()
    demo_multi_language()
    demo_confidence_threshold()
    
    print("\n" + "="*70)
    print("  ✅ Demo Complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

