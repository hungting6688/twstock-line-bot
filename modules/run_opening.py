from modules.signal_analysis import analyze_stocks_with_signals

def analyze_opening():
    print("📌 分析模式：opening（09:00 開盤推薦）")
    return analyze_stocks_with_signals(
        limit=100,             # 熱門前 100
        min_score=2.0,         # 推薦門檻
        filter_type="all"      # 所有股票類型
    )
