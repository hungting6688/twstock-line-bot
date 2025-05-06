print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import requests
import pandas as pd
from io import StringIO

def get_realtime_top_stocks(min_turnover=50000000, limit=100):
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"

    try:
        response = requests.get(url, timeout=10)
        response.encoding = "big5"

        lines = response.text.splitlines()
        cleaned_lines = [line for line in lines if line.count(",") >= 10]
        csv_data = "\n".join(cleaned_lines)

        df = pd.read_csv(StringIO(csv_data), thousands=",", engine="python", on_bad_lines="skip")
        df.columns = df.columns.str.strip()

        stock_col = [col for col in df.columns if "代號" in col][0]
        turnover_col = [col for col in df.columns if "成交金額" in col][0]

        df = df[[stock_col, turnover_col]]
        df.columns = ["stock_id", "turnover"]
        df["stock_id"] = df["stock_id"].astype(str).str.zfill(4)
        df["turnover"] = pd.to_numeric(df["turnover"], errors="coerce")

        df = df.dropna(subset=["turnover"])
        df = df[df["turnover"] > min_turnover]
        df = df.sort_values(by="turnover", ascending=False).head(limit)

        print(f"[price_fetcher] ✅ 成功取得熱門股 {len(df)} 檔")
        return df["stock_id"].tolist()

    except Exception as e:
        print(f"[price_fetcher] ❌ 資料解析失敗：{e}")
        return []