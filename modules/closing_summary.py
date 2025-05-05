# modules/closing_summary.py

from modules.signal_analysis import analyze_stocks_with_signals
from modules.stock_data_utils import get_all_stock_ids

def analyze_closing():
    title = "📉 收盤分析報告（含中長線潛力）"
    stock_ids = get_all_stock_ids(limit=300, filter_type="all")  # 保留 ETF，排除無效股
    return analyze_stocks_with_signals(
        stock_ids=stock_ids,
        title=title,
        min_score=2.5,
        include_weak=True
    )
