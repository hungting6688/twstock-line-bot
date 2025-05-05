# modules/dividend.py

from modules.signal_analysis import analyze_stocks_with_signals
from modules.stock_data_utils import get_all_stock_ids

def analyze_dividend():
    title = "📈 中午潛力股速報（含法人動向）"
    return analyze_stocks_with_signals(
        title=title,
        stock_ids=get_all_stock_ids(limit=150, filter_type="small_cap"),
        min_score=2.5
    )
