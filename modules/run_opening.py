
from modules.signal_analysis import analyze_stocks_with_signals

def analyze_opening(limit=100):
    return analyze_stocks_with_signals(title="📊 開盤推薦股報告", limit=limit)
