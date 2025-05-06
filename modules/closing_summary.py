# modules/closing_summary.py

print("[closing_summary] ✅ 已載入最新版")

from modules.signal_analysis import analyze_stocks_with_signals

def analyze_closing():
    return analyze_stocks_with_signals(
        mode="closing",
        limit=300,
        min_score=5,
        include_weak=True
    )
