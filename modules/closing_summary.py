# modules/closing_summary.py

from modules.signal_analysis import analyze_stocks_with_signals
from modules.stock_data_utils import get_latest_valid_trading_date
from datetime import datetime

def analyze_closing():
    print("📌 分析模式：closing")
    date = get_latest_valid_trading_date()

    return analyze_stocks_with_signals(
        title="📊 收盤推薦股報告",
        stock_ids=None,       # 自動抓熱門股＋Google Sheet
        limit=300,
        min_score=2.5,
        include_weak=True,
        filter_type="all",    # 不限股型，大中小全掃描
        date=date
    )
