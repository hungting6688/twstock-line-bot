# modules/intraday_monitor.py

from modules.signal_analysis import analyze_stocks_with_signals
from modules.stock_data_utils import get_latest_valid_trading_date
from datetime import datetime

def analyze_intraday():
    print("📌 分析模式：intraday")
    date = get_latest_valid_trading_date()

    return analyze_stocks_with_signals(
        title="⏱️ 盤中監控推薦股",
        stock_ids=None,       # 自動抓台股熱門股＋Google Sheet
        limit=100,
        min_score=2.0,
        include_weak=True,
        filter_type="all",
        date=date
    )
