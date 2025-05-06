# modules/price_fetcher.py
print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import yfinance as yf
import pandas as pd
import requests
from io import StringIO

def get_realtime_top_stocks(limit=100):
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"
    res = requests.get(url)
    raw_text = res.text

    # 清理 CSV 格式
    lines = [line for line in raw_text.split("\n") if len(line.split(",")) > 10]
    csv_data = "\n".join(lines)
    df = pd.read_csv(StringIO(csv_data))

    # 過濾與清理欄位
    df.columns = df.columns.str.strip()
    df = df.rename(columns={"證券代號": "stock_id", "成交金額(元)": "turnover"})

    df = df[["stock_id", "turnover"]].copy()
    df["stock_id"] = df["stock_id"].astype(str).str.zfill(4)
    df["turnover"] = pd.to_numeric(df["turnover"].astype(str).str.replace(",", ""), errors="coerce")

    # 過濾成交金額大於 5000 萬元的股票
    df = df[df["turnover"] > 50_000_000]

    # 排序後取前 N 名
    df = df.sort_values(by="turnover", ascending=False).head(limit)
    stock_ids = df["stock_id"].tolist()
    return stock_ids
