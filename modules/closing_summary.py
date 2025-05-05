from modules.signal_analysis import analyze_stocks_with_signals

def analyze_closing_summary():
    return analyze_stocks_with_signals(
        title="🔚 收盤潛力股分析",
        limit=300,
        min_score=2.5,
        filter_type="all",
        include_weak=True
    )
