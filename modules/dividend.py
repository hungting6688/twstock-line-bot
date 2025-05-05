# modules/dividend.py

from modules.signal_analysis import analyze_stocks_with_signals
from modules.stock_data_utils import get_latest_valid_trading_date, get_hot_stock_ids

def analyze_dividend():
    title = "💰 中午殖利率＋短線機會速報"
    return analyze_stocks_with_signals(
        title=title,
        limit=150,
        min_score=2.0,
        filter_type="small_cap"
    )
