from modules.signal_analysis import analyze_stocks_with_signals

def analyze_closing():
    title = "📉 收盤綜合推薦總結"
    return analyze_stocks_with_signals(
        title=title,
        limit=300,
        min_score=2.5,
        filter_type="large_cap"
    )
