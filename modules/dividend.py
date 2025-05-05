# modules/closing_summary.py

from modules.signal_analysis import analyze_stocks_with_signals
from modules.stock_data_utils import get_all_stock_ids

def analyze_closing():
    title = "📊 收盤強勢股總結"
    return analyze_stocks_with_signals(
        title=title,
        stock_ids=get_all_stock_ids(limit=300, filter_type="all"),
        min_score=2.5
    )
