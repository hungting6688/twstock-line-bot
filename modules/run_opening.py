from modules.signal_analysis import analyze_stocks_with_signals

def analyze_run_opening():
    return analyze_stocks_with_signals(
        title="📌 開盤推薦股報告",
        limit=100,
        min_score=2.0,
        filter_type="all",
        include_weak=True
    )
