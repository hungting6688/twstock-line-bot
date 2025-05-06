# modules/price_fetcher.py
print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import requests
import pandas as pd
from io import StringIO

def get_realtime_top_stocks(min_turnover=50000000, limit=100):
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"

    try:
        response = requests.get(url, timeout=10)
        response.encoding = "big5"

        # 過濾掉非表格內容的行（通常是說明或空行）
        cleaned_lines = [line for line in response.text.split("\n") if line.count(",") > 10]
        cleaned_csv = "\n".join(cleaned_lines)

        df = pd.read_csv(StringIO(cleaned_csv))
        df.columns = df.columns.str.strip()

        # 嘗試找出正確欄位名稱
        possible_columns = [
            ("證券代號", "成交金額"),
            ("股票代號", "成交金額(千元)")
        ]

        for stock_col, turnover_col in possible_columns:
            if stock_col in df.columns and turnover_col in df.columns:
                df = df[[stock_col, turnover_col]]
                df.columns = ["stock_id", "turnover"]
                break
        else:
            raise ValueError("❌ 無法找到適用的欄位名稱")

        df["stock_id"] = df["stock_id"].astype(str).str.zfill(4)
        df["turnover"] = pd.to_numeric(df["turnover"].astype(str).str.replace(",", ""), errors="coerce")
        df = df.dropna(subset=["turnover"])
        df = df[df["turnover"] > min_turnover]
        df = df.sort_values(by="turnover", ascending=False).head(limit)

        print(f"[price_fetcher] ✅ 成功取得熱門股 {len(df)} 檔")
        return df["stock_id"].tolist()

    except Exception as e:
        print(f"[price_fetcher] ❌ 資料解析失敗：{e}")
        return []