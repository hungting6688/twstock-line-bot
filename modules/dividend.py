# modules/dividend.py

from modules.signal_analysis import analyze_stocks_with_signals
from modules.stock_data_utils import get_all_stock_ids

def analyze_dividend():
    title = "📈 午盤推薦：小型股與法人/殖利率機會"
    stock_ids = get_all_stock_ids(limit=150, filter_type="small_cap")
    return analyze_stocks_with_signals(
        stock_ids=stock_ids,
        title=title,
        min_score=2.2,
        include_weak=True
    )
