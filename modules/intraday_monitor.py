# modules/intraday_monitor.py

from modules.signal_analysis import analyze_stocks_with_signals
from modules.stock_data_utils import get_all_stock_ids

def analyze_intraday():
    title = "🔍 盤中強勢股監控"
    return analyze_stocks_with_signals(
        title=title,
        stock_ids=get_all_stock_ids(limit=100, filter_type="small_cap"),
        min_score=2.5
    )
