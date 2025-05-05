# modules/run_opening.py

from modules.signal_analysis import analyze_stocks_with_signals
from modules.stock_data_utils import get_tracking_stock_ids, get_latest_valid_trading_date
from datetime import datetime

def analyze_opening():
    print("📌 分析模式：opening")
    date = get_latest_valid_trading_date()
    
    return analyze_stocks_with_signals(
        title="📊 開盤推薦股報告",
        stock_ids=None,  # 自動抓台股股票
        limit=100,  # 前 100 熱門股 + 自選股
        min_score=2.0,  # 推薦門檻
        include_weak=True,
        filter_type="all",
        date=date
    )
