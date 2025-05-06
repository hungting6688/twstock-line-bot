# modules/price_fetcher.py
print("[price_fetcher] ✅ 使用 JSON 版本（穩定）")

import requests
import pandas as pd

def get_realtime_top_stocks(min_turnover=50000000, limit=100):
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date=&type=ALL"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if not data.get("data5") or not data.get("fields5"):
            print("[price_fetcher] ❌ JSON 中找不到 data5 或 fields5")
            return []

        columns = data["fields5"]
        rows = data["data5"]
        df = pd.DataFrame(rows, columns=columns)

        df["證券代號"] = df["證券代號"].astype(str).str.zfill(4)
        df["成交金額(元)"] = (
            df["成交金額(元)"].str.replace(",", "", regex=False).astype(float)
        )

        df = df[df["成交金額(元)"] > min_turnover]
        df = df.sort_values(by="成交金額(元)", ascending=False).head(limit)

        print(f"[price_fetcher] ✅ 成功取得熱門股 {len(df)} 檔")
        return df["證券代號"].tolist()

    except Exception as e:
        print(f"[price_fetcher] ❌ JSON 解析失敗：{e}")
        return []