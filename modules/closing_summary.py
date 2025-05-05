from modules.signal_analysis import analyze_stocks_with_signals

def analyze_closing():
    print("📌 分析模式：closing（15:00 收盤綜合分析）")
    return analyze_stocks_with_signals(
        limit=300,             # 熱門前 300
        min_score=2.0,         # 推薦門檻
        filter_type="all"      # 所有股票納入
    )
