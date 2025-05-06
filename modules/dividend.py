# modules/dividend.py

print("[dividend] ✅ 已載入最新版")

from modules.signal_analysis import analyze_stocks_with_signals

def analyze_dividend():
    return analyze_stocks_with_signals(
        mode="dividend",
        limit=200,
        min_score=4,
        include_weak=True
    )
