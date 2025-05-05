from modules.signal_analysis import analyze_stocks_with_signals
from modules.stock_data_utils import get_latest_valid_trading_date

def analyze_opening():
    print("📌 分析模式：opening")
    title = "📊 開盤推薦股報告"

    return analyze_stocks_with_signals(
        title=title,
        min_score=2.0,
        limit=100,
        filter_type="all",
        include_weak=True,
        date=get_latest_valid_trading_date()
    )
