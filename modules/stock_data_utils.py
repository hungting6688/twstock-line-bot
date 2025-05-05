# modules/stock_data_utils.py

import datetime
import pandas as pd
import yfinance as yf

# 抓取所有上市上櫃股票（不含已下市）
def get_all_stock_ids(limit=None, filter_type="all"):
    from modules.twse_scraper import get_all_valid_twse_stocks
    all_stocks = get_all_valid_twse_stocks()

    # 篩選條件：依市值估算大小股
    if filter_type == "large_cap":
        filtered = [s for s in all_stocks if s["市值(億元)"] >= 300]
    elif filter_type == "small_cap":
        filtered = [s for s in all_stocks if s["市值(億元)"] < 300]
    else:
        filtered = all_stocks

    stock_ids = [s["股票代號"] for s in filtered if s["股票代號"].isdigit()]
    if limit:
        stock_ids = stock_ids[:limit]
    return stock_ids

# 🔁 保留以便日後調用
def get_hot_stock_ids(limit=100, filter_type="all"):
    return get_all_stock_ids(limit=limit, filter_type=filter_type)

# 尋找最近一個交易日（避免週末與國定假日）
def get_latest_valid_trading_date():
    today = datetime.date.today()
    for i in range(5):
        date = today - datetime.timedelta(days=i)
        if date.weekday() < 5:  # 週一～週五為有效交易日
            return date.strftime("%Y-%m-%d")
    return today.strftime("%Y-%m-%d")
