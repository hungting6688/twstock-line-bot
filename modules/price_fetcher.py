# modules/price_fetcher.py

import yfinance as yf
import pandas as pd

def fetch_price_data(stock_id: str):
    try:
        ticker = f"{stock_id}.TW"
        df = yf.download(ticker, period="90d", interval="1d", progress=False)
        df = df.rename(columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume"
        })
        df = df[["open", "high", "low", "close", "volume"]].dropna().reset_index()
        return df
    except Exception as e:
        print(f"⚠️ 無法取得 {stock_id} 資料：{e}")
        return None
