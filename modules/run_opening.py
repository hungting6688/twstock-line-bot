# modules/run_opening.py

from modules.signal_analysis import analyze_stocks_with_signals

def analyze_opening():
    return analyze_stocks_with_signals(
        mode="opening",
        limit=100,             # 掃描前 100 大熱門股
        min_score=2,           # 推薦門檻低，適合短線切入
        include_weak=True,     # 顯示極弱股
        filter_type=None       # 不限制股型
    )
