# multilingual_demo.py
import asyncio

try:
    from interruption_handler import InterruptionHandler, InterruptionConfig, Language
except Exception:
    # If your module doesn't have Language enum, try simpler import
    from interruption_handler import InterruptionHandler, InterruptionConfig

def make_mixed_handler():
    # Try to create mixed-language config if supported
    try:
        cfg = InterruptionConfig.from_languages(["mixed"])
        h = InterruptionHandler(cfg)
    except Exception:
        # fallback to manual words list
        words = ["uh","umm","hmm","haan","achha","yaar"]
        try:
            cfg = InterruptionConfig.from_word_list(words)
            h = InterruptionHandler(cfg)
        except Exception:
            h = InterruptionHandler()
    return h

async def run_demo():
    h = make_mixed_handler()
    print("\n=== Multilingual demo ===\n")
    cases = [
        ("uh haan", None),
        ("achha", None),
        ("hello namaste", None),
        ("umm okay stop", 0.9),
        ("haan wait", 0.9),
    ]
    for text, conf in cases:
        if conf is None:
            res = h.should_ignore_speech(text)
        else:
            res = h.should_ignore_speech(text, confidence=conf)
        print(f"'{text}' -> ignored? {res}")
    print("\n(Expect fillers like 'uh', 'haan', 'achha' to be ignored; mixes with 'wait/stop' not ignored)")

if __name__ == "__main__":
    asyncio.run(run_demo())
