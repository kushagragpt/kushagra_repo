"""
Test scenarios for the interruption handler.
Tests basic functionality, multi-language support, and runtime updates.
"""

from interruption_handler import InterruptionHandler, InterruptionConfig, Language


def test_filler_only_speech():
    """Test that filler-only speech is ignored."""
    config = InterruptionConfig.from_word_list(["uh", "umm", "hmm"])
    handler = InterruptionHandler(config)
    
    # Test cases that should be ignored
    assert handler.should_ignore_speech("uh") == True
    assert handler.should_ignore_speech("umm") == True
    assert handler.should_ignore_speech("uh umm") == True
    assert handler.should_ignore_speech("Uh, umm, hmm") == True
    
    print("✅ Filler-only speech test passed")


def test_mixed_speech():
    """Test that mixed speech with real words is not ignored."""
    config = InterruptionConfig.from_word_list(["uh", "umm", "hmm"])
    handler = InterruptionHandler(config)
    
    # Test cases that should NOT be ignored
    assert handler.should_ignore_speech("wait") == False
    assert handler.should_ignore_speech("stop") == False
    assert handler.should_ignore_speech("umm okay stop") == False
    assert handler.should_ignore_speech("uh wait a minute") == False
    
    print("✅ Mixed speech test passed")


def test_low_confidence_speech():
    """Test that low confidence speech is ignored."""
    config = InterruptionConfig.from_word_list(["uh"], confidence_threshold=0.5)
    handler = InterruptionHandler(config)
    
    # Low confidence should be ignored
    assert handler.should_ignore_speech("hello", confidence=0.3) == True
    assert handler.should_ignore_speech("hello", confidence=0.4) == True
    
    # High confidence should not be ignored
    assert handler.should_ignore_speech("hello", confidence=0.6) == False
    assert handler.should_ignore_speech("hello", confidence=0.9) == False
    
    print("✅ Low confidence speech test passed")


def test_background_murmur():
    """Test background murmur scenarios."""
    config = InterruptionConfig.from_word_list(["uh", "umm", "hmm", "yeah"], confidence_threshold=0.5)
    handler = InterruptionHandler(config)

    # Low confidence background noise - should be ignored due to low confidence
    assert handler.should_ignore_speech("hmm yeah", confidence=0.3) == True

    # Even with high confidence, if all words are fillers, should be ignored
    assert handler.should_ignore_speech("hmm yeah", confidence=0.7) == True

    # But real words with high confidence should not be ignored
    assert handler.should_ignore_speech("hello there", confidence=0.7) == False

    print("✅ Background murmur test passed")


def test_empty_and_punctuation():
    """Test empty strings and punctuation-only input."""
    config = InterruptionConfig.from_word_list(["uh"])
    handler = InterruptionHandler(config)
    
    # Empty and punctuation-only should be ignored
    assert handler.should_ignore_speech("") == True
    assert handler.should_ignore_speech("   ") == True
    assert handler.should_ignore_speech("...") == True
    assert handler.should_ignore_speech("!!!") == True
    
    print("✅ Empty and punctuation test passed")


def test_case_insensitivity():
    """Test that matching is case-insensitive."""
    config = InterruptionConfig.from_word_list(["uh", "umm"])
    handler = InterruptionHandler(config)
    
    # Different cases should all be ignored
    assert handler.should_ignore_speech("UH") == True
    assert handler.should_ignore_speech("Umm") == True
    assert handler.should_ignore_speech("UMM") == True
    assert handler.should_ignore_speech("uH uMm") == True
    
    print("✅ Case insensitivity test passed")


def test_dynamic_updates():
    """Test dynamic word list updates."""
    config = InterruptionConfig.from_word_list(
        ["uh"],
        enable_dynamic_updates=True
    )
    handler = InterruptionHandler(config)
    
    # Initially "hmm" should not be ignored (has real content)
    assert handler.should_ignore_speech("hmm") == False
    
    # Add "hmm" to ignored list
    handler.add_ignored_word("hmm")
    
    # Now "hmm" should be ignored
    assert handler.should_ignore_speech("hmm") == True
    
    # Remove "hmm" from ignored list
    handler.remove_ignored_word("hmm")
    
    # Now "hmm" should not be ignored again
    assert handler.should_ignore_speech("hmm") == False
    
    print("✅ Dynamic updates test passed")


def test_multilingual_fillers():
    """Test multilingual filler words."""
    config = InterruptionConfig.from_word_list(["uh", "umm", "haan", "hmm"])
    handler = InterruptionHandler(config)

    # Hindi filler
    assert handler.should_ignore_speech("haan") == True

    # Mixed language fillers
    assert handler.should_ignore_speech("uh haan") == True

    # Real Hindi word (not a filler)
    assert handler.should_ignore_speech("namaste") == False

    print("✅ Multilingual fillers test passed")


def test_language_presets_english():
    """Test English language preset."""
    config = InterruptionConfig.from_languages([Language.ENGLISH])
    handler = InterruptionHandler(config)

    # English fillers should be ignored
    assert handler.should_ignore_speech("uh") == True
    assert handler.should_ignore_speech("umm") == True
    assert handler.should_ignore_speech("you know") == True  # Multi-word filler
    assert handler.should_ignore_speech("i mean") == True  # Multi-word filler
    assert handler.should_ignore_speech("basically") == True
    assert handler.should_ignore_speech("like") == True
    assert handler.should_ignore_speech("uh like umm") == True  # All fillers

    # Real English words should not be ignored
    assert handler.should_ignore_speech("hello") == False
    assert handler.should_ignore_speech("wait") == False
    assert handler.should_ignore_speech("stop please") == False

    print("✅ English language preset test passed")


def test_language_presets_hindi():
    """Test Hindi language preset."""
    config = InterruptionConfig.from_languages([Language.HINDI])
    handler = InterruptionHandler(config)

    # Hindi fillers should be ignored
    assert handler.should_ignore_speech("haan") == True
    assert handler.should_ignore_speech("achha") == True
    assert handler.should_ignore_speech("matlab") == True
    assert handler.should_ignore_speech("theek") == True

    # Real Hindi words should not be ignored
    assert handler.should_ignore_speech("namaste") == False
    assert handler.should_ignore_speech("dhanyavaad") == False

    print("✅ Hindi language preset test passed")


def test_language_presets_mixed():
    """Test mixed language preset (English + Hindi)."""
    config = InterruptionConfig.from_languages([Language.MIXED])
    handler = InterruptionHandler(config)

    # Both English and Hindi fillers should be ignored
    assert handler.should_ignore_speech("uh") == True
    assert handler.should_ignore_speech("haan") == True
    assert handler.should_ignore_speech("uh haan") == True
    assert handler.should_ignore_speech("umm achha") == True
    assert handler.should_ignore_speech("like matlab") == True

    # Real words in either language should not be ignored
    assert handler.should_ignore_speech("hello") == False
    assert handler.should_ignore_speech("namaste") == False
    assert handler.should_ignore_speech("hello namaste") == False

    print("✅ Mixed language preset test passed")


def test_mixed_language_conversation():
    """Test realistic mixed English-Hindi conversation scenarios."""
    config = InterruptionConfig.from_languages([Language.MIXED])
    handler = InterruptionHandler(config)

    # Filler-only in mixed languages
    assert handler.should_ignore_speech("uh haan hmm") == True
    assert handler.should_ignore_speech("achha yeah umm") == True  # All fillers
    assert handler.should_ignore_speech("haan like matlab") == True  # All fillers

    # Real mixed language speech
    assert handler.should_ignore_speech("hello kaise ho") == False
    assert handler.should_ignore_speech("wait ruko") == False
    assert handler.should_ignore_speech("umm hello namaste") == False  # Has real words
    assert handler.should_ignore_speech("okay stop") == False  # "okay" is not a filler in our list

    print("✅ Mixed language conversation test passed")


def test_runtime_add_remove_words():
    """Test adding and removing words at runtime."""
    config = InterruptionConfig.from_word_list(["uh"], enable_dynamic_updates=True)
    handler = InterruptionHandler(config)

    # Initially "okay" is not ignored
    assert handler.should_ignore_speech("okay") == False

    # Add "okay" to ignored list
    success = handler.add_ignored_word("okay")
    assert success == True
    assert handler.should_ignore_speech("okay") == True

    # Try to add it again (should return False)
    success = handler.add_ignored_word("okay")
    assert success == False

    # Remove "okay"
    success = handler.remove_ignored_word("okay")
    assert success == True
    assert handler.should_ignore_speech("okay") == False

    # Try to remove it again (should return False)
    success = handler.remove_ignored_word("okay")
    assert success == False

    print("✅ Runtime add/remove words test passed")


def test_runtime_bulk_operations():
    """Test bulk add/remove operations."""
    config = InterruptionConfig.from_word_list(["uh"], enable_dynamic_updates=True)
    handler = InterruptionHandler(config)

    # Bulk add words
    words_to_add = ["okay", "right", "sure"]
    count = handler.add_ignored_words_bulk(words_to_add)
    assert count == 3

    # All should now be ignored
    assert handler.should_ignore_speech("okay") == True
    assert handler.should_ignore_speech("right") == True
    assert handler.should_ignore_speech("sure") == True

    # Bulk remove words
    words_to_remove = ["okay", "right"]
    count = handler.remove_ignored_words_bulk(words_to_remove)
    assert count == 2

    # These should not be ignored anymore
    assert handler.should_ignore_speech("okay") == False
    assert handler.should_ignore_speech("right") == False
    # But "sure" should still be ignored
    assert handler.should_ignore_speech("sure") == True

    print("✅ Runtime bulk operations test passed")


def test_runtime_add_language_preset():
    """Test adding language presets at runtime."""
    config = InterruptionConfig.from_word_list(["uh"], enable_dynamic_updates=True)
    handler = InterruptionHandler(config)

    # Initially Hindi fillers are not ignored
    assert handler.should_ignore_speech("haan") == False
    assert handler.should_ignore_speech("achha") == False

    # Add Hindi language preset
    count = handler.add_language_preset(Language.HINDI)
    assert count > 0  # Should add multiple words

    # Now Hindi fillers should be ignored
    assert handler.should_ignore_speech("haan") == True
    assert handler.should_ignore_speech("achha") == True

    print("✅ Runtime add language preset test passed")


def test_runtime_confidence_threshold_update():
    """Test updating confidence threshold at runtime."""
    config = InterruptionConfig.from_word_list(["uh"], enable_dynamic_updates=True, confidence_threshold=0.5)
    handler = InterruptionHandler(config)

    # With threshold 0.5, confidence 0.4 should be ignored
    assert handler.should_ignore_speech("hello", confidence=0.4) == True

    # Update threshold to 0.3
    success = handler.update_confidence_threshold(0.3)
    assert success == True

    # Now confidence 0.4 should not be ignored
    assert handler.should_ignore_speech("hello", confidence=0.4) == False

    # But confidence 0.2 should still be ignored
    assert handler.should_ignore_speech("hello", confidence=0.2) == True

    print("✅ Runtime confidence threshold update test passed")


def test_statistics_tracking():
    """Test that statistics are tracked correctly."""
    config = InterruptionConfig.from_word_list(["uh", "umm"], enable_dynamic_updates=True)
    handler = InterruptionHandler(config)

    # Process some speech
    handler.should_ignore_speech("uh")  # Filler
    handler.should_ignore_speech("hello")  # Valid
    handler.should_ignore_speech("umm")  # Filler
    handler.should_ignore_speech("wait", confidence=0.2)  # Low confidence
    handler.should_ignore_speech("stop")  # Valid

    stats = handler.get_stats()

    assert stats["statistics"]["total_speech_events"] == 5
    assert stats["statistics"]["ignored_filler_count"] == 2
    assert stats["statistics"]["ignored_low_confidence_count"] == 1
    assert stats["statistics"]["valid_interruptions"] == 2

    print("✅ Statistics tracking test passed")


def test_get_words_by_language():
    """Test getting words categorized by language."""
    # Use separate languages instead of MIXED to test categorization
    config = InterruptionConfig.from_languages(
        [Language.ENGLISH, Language.HINDI],
        enable_dynamic_updates=True
    )
    handler = InterruptionHandler(config)

    # Add a custom word
    handler.add_ignored_word("custom_word")

    words_by_lang = handler.get_ignored_words_by_language()

    # Should have English, Hindi, and custom categories
    assert "en" in words_by_lang
    assert "hi" in words_by_lang
    assert "custom" in words_by_lang

    # Custom word should be in custom category
    assert "custom_word" in words_by_lang["custom"]

    # Verify some expected words are in the right categories
    assert "uh" in words_by_lang["en"]
    assert "haan" in words_by_lang["hi"]

    print("✅ Get words by language test passed")


def run_all_tests():
    """Run all test scenarios."""
    print("\n" + "="*70)
    print("Running Interruption Handler Tests")
    print("="*70 + "\n")

    print("📋 Basic Functionality Tests")
    print("-" * 70)
    test_filler_only_speech()
    test_mixed_speech()
    test_low_confidence_speech()
    test_background_murmur()
    test_empty_and_punctuation()
    test_case_insensitivity()
    test_dynamic_updates()
    test_multilingual_fillers()

    print("\n📋 Multi-Language Support Tests")
    print("-" * 70)
    test_language_presets_english()
    test_language_presets_hindi()
    test_language_presets_mixed()
    test_mixed_language_conversation()

    print("\n📋 Runtime Update Tests")
    print("-" * 70)
    test_runtime_add_remove_words()
    test_runtime_bulk_operations()
    test_runtime_add_language_preset()
    test_runtime_confidence_threshold_update()

    print("\n📋 Advanced Features Tests")
    print("-" * 70)
    test_statistics_tracking()
    test_get_words_by_language()

    print("\n" + "="*70)
    print("🎉 All tests passed! ✅")
    print("="*70)
    print(f"Total tests run: 18")
    print("="*70 + "\n")


if __name__ == "__main__":
    run_all_tests()

