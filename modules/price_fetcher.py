# modules/price_fetcher.py

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from modules.twse_scraper import get_all_valid_twse_stocks
from modules.stock_data_utils import get_latest_valid_trading_date

def fetch_price_data(stock_id: str, date: str) -> pd.DataFrame:
    try:
        ticker = f"{stock_id}.TW"
        df = yf.download(ticker, start=date, end=date, progress=False, interval="1d")
        if df.empty:
            return None
        df.reset_index(inplace=True)
        df["stock_id"] = stock_id
        return df
    except Exception as e:
        print(f"⚠️ 無法取得 {stock_id} 的價格資料：{e}")
        return None

def fetch_multiple_stock_prices(stock_ids: list, date: str) -> pd.DataFrame:
    all_data = []
    for sid in stock_ids:
        df = fetch_price_data(sid, date)
        if df is not None:
            all_data.append(df)
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        return pd.DataFrame()

def get_top_n_hot_stocks(n=100) -> list:
    return get_all_valid_twse_stocks()[:n]

def get_all_stock_price_data(limit=100, filter_type="all") -> pd.DataFrame:
    date = get_latest_valid_trading_date()
    stock_ids = get_all_valid_twse_stocks(limit=limit, filter_type=filter_type)
    return fetch_multiple_stock_prices(stock_ids, date)
