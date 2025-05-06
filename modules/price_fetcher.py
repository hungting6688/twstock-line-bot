# modules/price_fetcher.py
print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import pandas as pd
import requests
from io import StringIO
import datetime

def get_realtime_top_stocks(min_turnover=50000000):
    try:
        today = datetime.datetime.today().strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={today}&type=ALL"

        response = requests.get(url)
        csv_data = "\n".join([line for line in response.text.splitlines() if line.count(",") > 6])
        df = pd.read_csv(StringIO(csv_data))

        df.columns = df.columns.str.strip()
        df = df.rename(columns={"證券代號": "stock_id", "成交股數": "Volume", "收盤價": "Close"})

        df = df[["stock_id", "Volume", "Close"]].dropna()
        df["Volume"] = pd.to_numeric(df["Volume"].astype(str).str.replace(",", ""), errors="coerce")
        df["Close"] = pd.to_numeric(df["Close"].astype(str).str.replace(",", ""), errors="coerce")
        df = df.dropna()

        df["turnover"] = df["Volume"] * df["Close"]
        df["stock_id"] = df["stock_id"].astype(str).str.zfill(4)

        # 篩掉成交金額太小的
        df = df[df["turnover"] >= min_turnover]

        # 排除下市股票（代碼非數字者）但保留 ETF
        df = df[df["stock_id"].str.match(r"^\d+$")]

        top_stocks = df.sort_values(by="turnover", ascending=False).head(300)
        return top_stocks["stock_id"].tolist()
    except Exception as e:
        print(f"[price_fetcher] ❌ 資料解析失敗：{e}")
        return []