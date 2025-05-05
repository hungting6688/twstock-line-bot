from modules.finmind_utils import (
    get_latest_valid_trading_date,
    fetch_finmind_data,
    fetch_stock_technical_data,
    get_hot_stock_ids
)

def analyze_intraday():
    title = "📍 盤中監控速報"
    return analyze_stocks_with_signals(
        title=title,
        limit=100,
        min_score=1.5,
        filter_type="all"
    )
