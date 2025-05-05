from modules.finmind_utils import (
    get_latest_valid_trading_date,
    fetch_finmind_data,
    fetch_stock_technical_data,
    get_hot_stock_ids
)


def analyze_dividend():
    title = "💰 中午潛力股速報"
    return analyze_stocks_with_signals(
        title=title,
        limit=150,
        min_score=1.5,
        filter_type="small_cap"
    )
