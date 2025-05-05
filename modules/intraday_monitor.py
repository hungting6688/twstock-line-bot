from modules.signal_analysis import analyze_stocks_with_signals

def analyze_intraday():
    title = "📍 盤中監控速報"
    return analyze_stocks_with_signals(
        title=title,
        limit=100,
        min_score=1.5,
        filter_type="all"
    )
