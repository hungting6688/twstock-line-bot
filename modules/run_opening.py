from modules.signal_analysis import analyze_stocks_with_signals

def analyze_opening():
    title = "📌 開盤推薦股報告"
    return analyze_stocks_with_signals(
        title=title,
        limit=100,
        min_score=2.0,
        filter_type="all"
    )
