from modules.finmind_utils import (
    get_latest_valid_trading_date,
    fetch_finmind_data,
    fetch_stock_technical_data,
    get_hot_stock_ids
)

def analyze_closing():
    title = "📉 收盤綜合推薦總結"
    return analyze_stocks_with_signals(
        title=title,
        limit=300,
        min_score=2.5,
        filter_type="large_cap"
    )
