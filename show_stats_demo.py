# show_stats_demo.py
try:
    from interruption_handler import InterruptionHandler, InterruptionConfig
except Exception:
    from interruption_handler import InterruptionHandler as InterruptionHandler

def main():
    try:
        cfg = InterruptionConfig.from_word_list(["uh","umm","hmm"])
        h = InterruptionHandler(cfg)
    except Exception:
        h = InterruptionHandler()
    print("\n=== Stats demo ===")
    try:
        stats = h.get_stats()
        print("Stats:", stats)
    except Exception as e:
        print("No stats API available:", e)

if __name__ == "__main__":
    main()
