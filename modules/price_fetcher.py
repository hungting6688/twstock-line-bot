# ✅ price_fetcher.py（包含基本技術指標）
import pandas as pd
import requests
from io import StringIO
from datetime import datetime

def fetch_price_data(min_turnover=40000000, limit=100):
    print("[price_fetcher] ✅ 使用 TWSE CSV 報表穩定解析版本")
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX20?response=csv&date={}&type=ALL".format(
        datetime.today().strftime("%Y%m%d")
    )

    res = requests.get(url)
    lines = res.text.split("\n")
    clean_lines = [line for line in lines if line.count(",") > 10 and '證券代號' not in line]
    csv_text = "\n".join(clean_lines)
    df = pd.read_csv(StringIO(csv_text))

    df.columns = df.columns.str.strip()
    df = df.rename(columns={"證券代號": "stock_id", "證券名稱": "stock_name", "收盤價": "close", "成交股數": "volume", "成交金額": "turnover"})

    df = df[df["stock_id"].astype(str).str.isnumeric()]  # 僅保留正常股票
    df = df.copy()
    df["turnover"] = df["turnover"].replace({"--": "0", ",": ""}, regex=True).astype(float)
    df["close"] = df["close"].replace({"--": "0", ",": ""}, regex=True).astype(float)
    df = df[df["turnover"] >= min_turnover]

    df = df.sort_values("turnover", ascending=False).head(limit).reset_index(drop=True)

    # ✅ 加入基本技術指標欄位
    df["ma20"] = df["close"].rolling(window=20, min_periods=1).mean()
    df["bollinger_mid"] = df["ma20"]
    df["bollinger_std"] = df["close"].rolling(window=20, min_periods=1).std()
    df["macd_ema12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["macd_ema26"] = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = df["macd_ema12"] - df["macd_ema26"]
    df["macd_signal_line"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["kdj_k"] = df["close"].rolling(window=9, min_periods=1).mean()
    df["kdj_d"] = df["kdj_k"].rolling(window=3, min_periods=1).mean()
    df["rsi"] = 50  # 可實作完整 RSI 計算邏輯

    return df
