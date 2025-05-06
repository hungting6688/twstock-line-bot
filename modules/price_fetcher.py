import requests
import pandas as pd
from io import StringIO

def get_realtime_top_stocks(limit=100):
    print("[price_fetcher] ⚙️ 正在抓取即時熱門股資料")
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"

    try:
        res = requests.get(url)
        res.encoding = "big5"  # TWSE 是 big5 編碼

        csv_data = res.text
        # 加上 on_bad_lines="skip" 以跳過錯誤行（pandas >= 1.3.0）
        df = pd.read_csv(StringIO(csv_data), on_bad_lines="skip")

        df.columns = df.columns.str.strip()
        df = df.rename(columns={
            "證券代號": "stock_id",
            "成交股數": "volume",
            "成交金額": "turnover",
        })

        df = df[["stock_id", "turnover"]].dropna()
        df["turnover"] = pd.to_numeric(df["turnover"].astype(str).str.replace(",", ""), errors="coerce")
        df = df.dropna(subset=["turnover"])
        df["stock_id"] = df["stock_id"].astype(str).str.zfill(4)

        # 排除成交金額為 0 的股票
        df = df[df["turnover"] > 0]
        top_stocks = df.sort_values("turnover", ascending=False).head(limit)
        return top_stocks["stock_id"].tolist()

    except Exception as e:
        print(f"[price_fetcher] ❌ 資料解析失敗：{e}")
        return []