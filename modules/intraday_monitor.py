# modules/intraday_monitor.py

print("[intraday_monitor] ✅ 已載入最新版")

from modules.signal_analysis import analyze_stocks_with_signals

def analyze_intraday():
    return analyze_stocks_with_signals(
        mode="intraday",
        limit=150,
        min_score=4,
        include_weak=True
    )
