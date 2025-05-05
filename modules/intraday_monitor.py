from modules.signal_analysis import analyze_stocks_with_signals
from modules.stock_data_utils import get_latest_valid_trading_date

def analyze_intraday():
    print("📌 分析模式：intraday")
    title = "📊 盤中監控推薦（10:30）"

    return analyze_stocks_with_signals(
        title=title,
        limit=100,
        min_score=2.0,
        filter_type="small_cap",  # 專注觀察中小型股短線變化
        include_weak=True,
        date=get_latest_valid_trading_date()
    )
