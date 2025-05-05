# modules/stock_data_utils.py

from modules.hot_stock_scraper import fetch_top_100_volume_stocks
import datetime

def get_latest_valid_trading_date(offset_days=0):
    """
    傳回最近的有效交易日（排除假日），預設為今日，可設定往前幾天作保險。
    """
    today = datetime.date.today() - datetime.timedelta(days=offset_days)
    while today.weekday() >= 5:  # 5=Saturday, 6=Sunday
        today -= datetime.timedelta(days=1)
    return today.strftime("%Y-%m-%d")

def get_hot_stock_ids(limit=100, filter_type="all"):
    """
    使用證交所成交量排行取得熱門股代碼
    filter_type: 'all' | 'large_cap' | 'small_cap'
    """
    stock_ids = fetch_top_100_volume_stocks()
    if filter_type == "large_cap":
        return [sid for sid in stock_ids if sid.startswith("2")][:limit]
    elif filter_type == "small_cap":
        return [sid for sid in stock_ids if not sid.startswith("2")][:limit]
    return stock_ids[:limit]
