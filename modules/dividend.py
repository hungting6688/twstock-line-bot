from modules.signal_analysis import analyze_stocks_with_signals

def analyze_dividend():
    print("📌 分析模式：dividend（12:00 法人+殖利率推薦）")
    return analyze_stocks_with_signals(
        limit=100,               # 熱門前 100
        min_score=2.0,           # 推薦門檻
        filter_type="small_cap"  # 中小型股優先
    )
