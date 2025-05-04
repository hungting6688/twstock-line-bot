
from modules.signal_analysis import analyze_stocks_with_signals

def analyze_intraday(limit=100):
    return analyze_stocks_with_signals(title="📡 盤中技術快訊", limit=limit)

