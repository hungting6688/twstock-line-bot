# modules/price_fetcher.py
print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import requests
import pandas as pd

def get_top_stocks(limit=100, filter_type=None):
    try:
        url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date=&type=ALL"
        res = requests.get(url, timeout=10)
        data = res.json()

        found = False
        for table in data.get("tables", []):
            df = pd.DataFrame(table.get("data", []), columns=table.get("fields", []))
            if "證券代號" in df.columns and "成交金額" in df.columns:
                found = True
                break

        if not found:
            raise ValueError("無法找到包含成交金額的表格")

        df["成交金額"] = pd.to_numeric(df["成交金額"].str.replace(",", ""), errors="coerce")
        df = df.dropna(subset=["成交金額"])
        df = df.sort_values(by="成交金額", ascending=False)

        df["證券代號"] = df["證券代號"].astype(str)
        all_ids = df["證券代號"].tolist()

        if filter_type == "small_cap":
            return all_ids[50:50 + limit]
        elif filter_type == "large_cap":
            return all_ids[:limit]
        else:
            return all_ids[:limit]

    except Exception as e:
        print(f"[price_fetcher] ⚠️ 熱門股讀取失敗：{e}")
        return ["2330", "2317", "2454", "2303", "2882"][:limit]
