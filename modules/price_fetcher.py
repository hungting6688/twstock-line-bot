# modules/price_fetcher.py
print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import requests
import pandas as pd

def get_top_stocks(limit=100, filter_type=None):
    try:
        url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date=&type=ALL"
        res = requests.get(url, timeout=10)
        data = res.json()

        # 找到成交金額資料的 table
        for table in data["tables"]:
            df = pd.DataFrame(table["data"], columns=table["fields"])
            if "證券代號" in df.columns and "成交金額" in df.columns:
                break
        else:
            raise ValueError("無法找到有效的熱門股資料")

        df["成交金額"] = pd.to_numeric(df["成交金額"].str.replace(",", ""), errors="coerce")
        df = df.sort_values(by="成交金額", ascending=False)

        df["證券代號"] = df["證券代號"].astype(str)
        all_ids = df["證券代號"].tolist()

        print("[price_fetcher] 🔍 熱門股前幾筆資料預覽：")
        print(df[["證券代號", "證券名稱", "成交金額"]].head(10))

        if filter_type == "small_cap":
            return all_ids[50:50+limit]
        elif filter_type == "large_cap":
            return all_ids[:limit]
        else:
            return all_ids[:limit]

    except Exception as e:
        print(f"[price_fetcher] ⚠️ 熱門股讀取失敗：{e}")
        return ["2330", "2317", "2454", "2303", "2882"][:limit]
