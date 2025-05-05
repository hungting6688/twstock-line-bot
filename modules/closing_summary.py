# modules/closing_summary.py

from modules.signal_analysis import analyze_stocks_with_signals
from modules.stock_data_utils import get_latest_valid_trading_date, get_hot_stock_ids

def analyze_closing():
    title = "📊 收盤分析報告"
    return analyze_stocks_with_signals(
        title=title,
        limit=300,
        min_score=2.5,
        filter_type="all"
    )
