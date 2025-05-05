from modules.signal_analysis import analyze_stocks_with_signals
from modules.stock_data_utils import (
    get_tracking_stock_ids,
    get_latest_valid_trading_date,
    get_all_stock_ids,
)

def analyze_closing():
    print("📌 分析模式：closing")

    date = get_latest_valid_trading_date()
    tracked_ids = get_tracking_stock_ids()
    hot_ids = get_all_stock_ids(limit=300, filter_type="all")  # 全部熱門股（含大型+中小型）
    stock_ids = list(set(tracked_ids + hot_ids))

    return analyze_stocks_with_signals(
        date=date,
        stock_ids=stock_ids,
        title="📉 收盤總結與潛力股推薦",
        min_score=2.5,
        include_weak=True
    )
