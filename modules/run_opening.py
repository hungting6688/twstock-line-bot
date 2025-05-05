from modules.signal_analysis import analyze_stocks_with_signals
from modules.stock_data_utils import (
    get_tracking_stock_ids,
    get_latest_valid_trading_date,
    get_all_stock_ids,
)

def analyze_opening():
    print("📌 分析模式：opening")

    # 抓今天日期（避免是假日或週末）
    date = get_latest_valid_trading_date()

    # 從 Google Sheets 抓自選追蹤股（可為空）
    tracked_ids = get_tracking_stock_ids()

    # 自動抓取熱門股票（例如前100大）
    hot_ids = get_all_stock_ids(limit=100, filter_type="all")

    # 合併追蹤清單與熱門股
    stock_ids = list(set(tracked_ids + hot_ids))

    return analyze_stocks_with_signals(
        date=date,
        stock_ids=stock_ids,
        title="📊 開盤推薦股報告",
        min_score=2.0,
        include_weak=True
    )
