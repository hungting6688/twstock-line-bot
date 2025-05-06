print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import yfinance as yf
import pandas as pd
import requests
from io import StringIO

def get_realtime_top_stocks(limit=100):
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"
    try:
        res = requests.get(url)
        raw_text = res.text

        # 只保留有意義的資料行
        lines = raw_text.splitlines()
        clean_lines = [line for line in lines if line.count(",") > 10 and ("證券代號" in line or line[:4].isdigit())]
        csv_data = "\n".join(clean_lines)

        # 轉成 DataFrame
        df = pd.read_csv(StringIO(csv_data))
        df.columns = df.columns.str.strip()
        df = df.rename(columns={"證券代號": "stock_id", "成交金額(元)": "turnover"})

        df = df[["stock_id", "turnover"]].copy()
        df["stock_id"] = df["stock_id"].astype(str).str.zfill(4)
        df["turnover"] = pd.to_numeric(df["turnover"].astype(str).str.replace(",", ""), errors="coerce")
        df = df.dropna(subset=["turnover"])
        df = df[df["turnover"] > 50_000_000]  # 只取成交金額大於五千萬者
        df = df.sort_values(by="turnover", ascending=False).head(limit)

        print(f"[price_fetcher] ✅ 已抓取熱門股前 {len(df)} 檔")
        return df["stock_id"].tolist()

    except Exception as e:
        print(f"[price_fetcher] ❌ 資料解析失敗：{e}")
        return []
