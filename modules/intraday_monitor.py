# modules/intraday_monitor.py

from modules.signal_analysis import analyze_stocks_with_signals
from modules.stock_data_utils import get_all_stock_ids

def analyze_intraday():
    title = "📊 盤中監控速報"
    stock_ids = get_all_stock_ids(limit=150, filter_type="all")
    return analyze_stocks_with_signals(
        stock_ids=stock_ids,
        title=title,
        min_score=2.0,
        include_weak=True
    )
