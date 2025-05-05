from modules.signal_analysis import analyze_stocks_with_signals
from modules.stock_data_utils import (
    get_tracking_stock_ids,
    get_latest_valid_trading_date,
    get_all_stock_ids,
)

def analyze_dividend():
    print("📌 分析模式：dividend")

    date = get_latest_valid_trading_date()
    tracked_ids = get_tracking_stock_ids()
    hot_ids = get_all_stock_ids(limit=100, filter_type="small_cap")  # 專注中小型股
    stock_ids = list(set(tracked_ids + hot_ids))

    return analyze_stocks_with_signals(
        date=date,
        stock_ids=stock_ids,
        title="📊 中午股息與中小型觀察股",
        min_score=2.0,
        include_weak=True
    )
