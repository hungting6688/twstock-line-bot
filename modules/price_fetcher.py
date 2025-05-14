# modules/price_fetcher.py
print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import pandas as pd
from datetime import datetime
import requests
from io import StringIO

def fetch_price_data(stock_ids=None):
    """暫不處理個股歷史價格（已棄用），統一交由 signal_analysis 管理"""
    return {}

def fetch_top_stocks_from_twse(min_turnover=50000000):
    print("[price_fetcher] 🔍 從 TWSE 擷取即時熱門股資料...")

    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"
    response = requests.get(url)
    csv_text = "\n".join([line for line in response.text.splitlines() if len(line.split('","')) > 10])
    df = pd.read_csv(StringIO(csv_text))

    df = df.rename(columns=lambda x: x.strip())
    df = df[["證券代號", "證券名稱", "成交金額"]].copy()
    df["成交金額"] = pd.to_numeric(df["成交金額"].astype(str).str.replace(",", ""), errors="coerce")
    df = df.dropna(subset=["成交金額"])
    df = df[df["成交金額"] > min_turnover]
    df = df.reset_index(drop=True)

    print(f"[price_fetcher] ✅ 熱門股數量：{len(df)}")
    return df
