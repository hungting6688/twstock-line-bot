print("[price_fetcher] ✅ 載入強化版 (含原始內容解析預覽)")

import requests
import pandas as pd
from io import StringIO

def get_realtime_top_stocks(min_turnover=50000000, limit=100):
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"

    try:
        response = requests.get(url, timeout=10)
        response.encoding = "big5"

        if not response.text.strip():
            print("[price_fetcher] ❌ 回傳內容為空")
            return []

        print(f"[price_fetcher] 原始資料首 5 行：\n{''.join(response.text.splitlines()[:5])}")

        lines = response.text.splitlines()
        cleaned_lines = [line for line in lines if line.count(",") >= 10]
        csv_data = "\n".join(cleaned_lines)

        df = pd.read_csv(StringIO(csv_data), thousands=",", engine="python", on_bad_lines="skip")
        df.columns = df.columns.str.strip()

        stock_col = next((col for col in df.columns if "代號" in col), None)
        turnover_col = next((col for col in df.columns if "成交金額" in col), None)

        if not stock_col or not turnover_col:
            print(f"[price_fetcher] ❌ 找不到必要欄位（代號或成交金額）")
            print(f"[price_fetcher] 欄位清單：{df.columns.tolist()}")
            return []

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