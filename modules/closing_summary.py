from modules.stock_data_utils import get_latest_valid_trading_date, get_all_stock_ids
from modules.signal_analysis import analyze_stocks_with_signals

def analyze_closing():
    date = get_latest_valid_trading_date()
    stock_ids = get_all_stock_ids(limit=300, filter_type="all")
    title = f"📉 收盤綜合分析（{date}）"

    return analyze_stocks_with_signals(
        stock_ids=stock_ids,
        date=date,
        title=title,
        min_score=2.5,
        include_weak=True
    )
