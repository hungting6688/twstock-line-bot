from modules.signal_analysis import analyze_stocks_with_signals
from modules.stock_data_utils import get_latest_valid_trading_date

def analyze_closing():
    print("📌 分析模式：closing")
    title = "📊 收盤潛力股總結推薦（15:00）"

    return analyze_stocks_with_signals(
        title=title,
        limit=300,  # 擴大涵蓋範圍
        min_score=3.0,
        filter_type="all",  # 全部股票（含 ETF）
        include_weak=True,
        date=get_latest_valid_trading_date()
    )
