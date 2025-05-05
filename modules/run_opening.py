from modules.signal_analysis import analyze_stocks_with_signals

def analyze_opening():
    print("📌 分析模式：opening（09:00 開盤推薦）")
    return analyze_stocks_with_signals(
        limit=100,             # 前 100 大熱門股
        min_score=2.0,         # 推薦門檻
        filter_type="all"      # 不限大小型股
    )
