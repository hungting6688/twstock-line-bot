
from modules.signal_analysis import analyze_stocks_with_signals

def analyze_dividend(limit=100):
    return analyze_stocks_with_signals(title="📈 中午短線潛力股速報", limit=limit)
