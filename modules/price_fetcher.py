import yfinance as yf
import pandas as pd

def fetch_price_data(stock_id: str, start: str, end: str) -> pd.DataFrame:
    ticker = f"{stock_id}.TW"
    df = yf.download(ticker, start=start, end=end)
    df.reset_index(inplace=True)
    df.rename(columns={
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    }, inplace=True)
    df["stock_id"] = stock_id
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df[["stock_id", "date", "open", "high", "low", "close", "volume"]]
