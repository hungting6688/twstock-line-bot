from modules.signal_analysis import analyze_stocks_with_signals
from modules.finmind_utils import (
    get_latest_valid_trading_date,
    fetch_finmind_data,
    fetch_stock_technical_data,
    get_hot_stock_ids
)

def analyze_closing():
    title = "📊 收盤綜合分析\n"
    body = analyze_stocks_with_signals(
        limit=300,
        min_score=2.0,
        filter_type="all"
    )
    return title + body

