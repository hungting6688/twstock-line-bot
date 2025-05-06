# modules/run_opening.py

from modules.signal_analysis import analyze_stocks_with_signals

def analyze_opening():
    return analyze_stocks_with_signals(
        mode="opening",
        limit=100,
        min_score=2,
        include_weak=True,
        filter_type=None
    )
