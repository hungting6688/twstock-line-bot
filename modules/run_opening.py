from modules.stock_data_utils import get_latest_valid_trading_date, get_all_stock_ids
from modules.signal_analysis import analyze_stocks_with_signals

def analyze_opening():
    date = get_latest_valid_trading_date()
    stock_ids = get_all_stock_ids(limit=100, filter_type="all")  # 熱門前 100 檔，保留 ETF
    title = f"📌 開盤推薦股報告（{date}）"

    return analyze_stocks_with_signals(
        stock_ids=stock_ids,
        date=date,
        title=title,
        min_score=2.0,
        include_weak=True
    )
