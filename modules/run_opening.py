# modules/run_opening.py

from modules.signal_analysis import analyze_stocks_with_signals

def analyze_opening():
    return analyze_stocks_with_signals(
        mode="opening",
        limit=5,           # 少量測試
        min_score=3,
        include_weak=True,
        filter_type=None
    )
