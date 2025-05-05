from modules.signal_analysis import analyze_stocks_with_signals

def analyze_dividend():
    title = "💰 中午潛力股速報"
    return analyze_stocks_with_signals(title=title, limit=150)
