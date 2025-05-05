# modules/intraday_monitor.py

from modules.signal_analysis import analyze_stocks_with_signals
from modules.stock_data_utils import get_latest_valid_trading_date, get_hot_stock_ids

def analyze_intraday():
    title = "⏰ 盤中監控速報"
    return analyze_stocks_with_signals(
        title=title,
        limit=120,
        min_score=2.0,
        filter_type="all"
    )
