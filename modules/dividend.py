from modules.signal_analysis import analyze_stocks_with_signals
from modules.stock_data_utils import get_latest_valid_trading_date

def analyze_dividend():
    print("📌 分析模式：dividend")
    title = "📊 午盤殖利率法人潛力推薦（12:00）"

    return analyze_stocks_with_signals(
        title=title,
        limit=150,
        min_score=2.5,
        filter_type="small_cap",  # 著重中小型股短線或轉機潛力
        include_weak=True,
        date=get_latest_valid_trading_date()
    )
