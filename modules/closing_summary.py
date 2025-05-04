
from modules.signal_analysis import analyze_stocks_with_signals

def analyze_closing(limit=300):
    return analyze_stocks_with_signals(title="📉 收盤潛力股整理", limit=limit)

