from modules.signal_analysis import analyze_stocks_with_signals

def analyze_intraday():
    print("📌 分析模式：intraday（10:30 盤中監控）")
    return analyze_stocks_with_signals(
        limit=100,            # 前 100 大熱門股
        min_score=1.5,        # 推薦門檻放寬
        filter_type="all"     # 大中小型皆可
    )
