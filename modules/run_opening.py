# modules/run_opening.py
print("[run_opening] ✅ 已載入最新版")

from modules.signal_analysis import analyze_stocks_with_signals

def analyze_opening():
    return analyze_stocks_with_signals(
        mode="opening",
        limit=100,
        min_score=3.5,
        filter_type=None,
        include_weak=True
    )
