# modules/run_opening.py

from modules.signal_analysis import analyze_stocks_with_signals

def analyze_opening():
    return analyze_stocks_with_signals(
        mode="opening",
        limit=100,               # 掃描前 100 檔熱門股
        min_score=3,             # ✅ 降低推薦門檻（原本是 5）
        include_weak=True,
        filter_type=None
    )
