# ✅ price_fetcher.py（根據 strategy 自動產生技術指標）
import pandas as pd
import requests
from io import StringIO
from datetime import datetime

def fetch_price_data(min_turnover=40000000, limit=100, mode="opening", strategy=None):
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

    df = df[df["stock_id"].astype(str).str.isnumeric()]
    df = df.copy()
    df["turnover"] = df["turnover"].replace({"--": "0", ",": ""}, regex=True).astype(float)
    df["close"] = df["close"].replace({"--": "0", ",": ""}, regex=True).astype(float)
    df = df[df["turnover"] >= min_turnover]
    df = df.sort_values("turnover", ascending=False).head(limit).reset_index(drop=True)

    # 技術指標參數從 strategy 取得
    if strategy is None:
        strategy = {}

    # RSI
    rsi_period = strategy.get("rsi_period", 9)
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=rsi_period, min_periods=1).mean()
    avg_loss = loss.rolling(window=rsi_period, min_periods=1).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df["rsi"] = 100 - (100 / (1 + rs))

    # MA
    ma_periods = strategy.get("ma_periods", [20])
    for p in ma_periods:
        df[f"ma{p}"] = df["close"].rolling(window=p, min_periods=1).mean()

    # MACD
    fast = strategy.get("macd_fast", 12)
    slow = strategy.get("macd_slow", 26)
    signal = strategy.get("macd_signal", 9)
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    df["macd"] = ema_fast - ema_slow
    df["macd_signal_line"] = df["macd"].ewm(span=signal, adjust=False).mean()

    # KDJ（模擬版）
    df["kdj_k"] = df["close"].rolling(window=9, min_periods=1).mean()
    df["kdj_d"] = df["kdj_k"].rolling(window=3, min_periods=1).mean()

    return df
