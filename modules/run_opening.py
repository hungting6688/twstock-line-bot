from modules.signal_analysis import analyze_stocks_with_signals

def analyze_opening():
    title = "📌 開盤推薦股報告"
    result = analyze_stocks_with_signals(title=title, limit=100)
    return result
