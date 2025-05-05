from modules.signal_analysis import analyze_stocks_with_signals

def analyze_intraday_monitor():
    return analyze_stocks_with_signals(
        title="📍 盤中監控推薦股",
        limit=100,
        min_score=2.5,
        filter_type="all",
        include_weak=True
    )
