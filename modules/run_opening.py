print("[run_opening] ✅ 已載入最新版")

from modules.signal_analysis import analyze_stocks_with_signals

def analyze_opening(limit=None, min_score=None, include_weak=None):
    return analyze_stocks_with_signals(
        mode="opening",
        limit=limit,
        min_score=min_score,
        include_weak=include_weak
    )
