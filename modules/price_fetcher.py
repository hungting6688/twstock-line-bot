import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_price_data(stock_id, start_date=None, end_date=None):
    
    stock_code = f"{stock_id}.TW"
    if end_date is None:
        end_date = datetime.today().strftime('%Y-%m-%d')
    if start_date is None:
        start_date = (datetime.today() - timedelta(days=180)).strftime('%Y-%m-%d')

    try:
        df = yf.download(stock_code, start=start_date, end=end_date)
        df = df.rename(columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume"
        })
        df.reset_index(inplace=True)
        df["date"] = df["Date"].dt.strftime("%Y-%m-%d")
        df = df[["date", "open", "high", "low", "close", "volume"]]
        return df
    except Exception as e:
        print(f"❌ Yahoo Finance 抓取失敗：{stock_id} | {e}")
        return pd.DataFrame()
