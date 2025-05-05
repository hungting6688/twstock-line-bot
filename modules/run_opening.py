# modules/run_opening.py

from modules.signal_analysis import analyze_stocks_with_signals
from modules.stock_data_utils import get_latest_valid_trading_date, get_all_stock_ids

def analyze_opening():
    title = "📌 開盤推薦股報告"
    return analyze_stocks_with_signals(
        title=title,
        stock_ids=get_all_stock_ids(limit=100, filter_type="all"),
        min_score=2.0
    )
