print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import requests
import pandas as pd
from io import StringIO
from datetime import datetime

def fetch_price_data(limit=100):
    print("[price_fetcher] ⏳ 擷取台股熱門股清單（來自 TWSE CSV）...")
    try:
        url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={}&type=ALL".format(datetime.today().strftime("%Y%m%d"))
        response = requests.get(url, timeout=10)
        content = response.text

        # 移除開頭與非資料列
        lines = [line for line in content.split('\n') if line.count(',') > 10]
        csv_data = '\n'.join(lines)
        df = pd.read_csv(StringIO(csv_data))

        df = df.rename(columns={
            df.columns[0]: "證券代號",
            df.columns[1]: "證券名稱",
            df.columns[2]: "成交股數",
            df.columns[4]: "成交金額"
        })

        # 處理逗號與無效值
        df = df.dropna(subset=["證券代號", "成交金額"])
        df["成交金額"] = df["成交金額"].astype(str).str.replace(",", "", regex=False)
        df["成交金額"] = pd.to_numeric(df["成交金額"], errors="coerce")
        df = df.dropna(subset=["成交金額"])

        # 排除 ETF（證券代號為非數字）
        df = df[df["證券代號"].astype(str).str.isnumeric()]

        # 篩選成交金額前 limit 檔
        df = df.sort_values(by="成交金額", ascending=False).head(limit)
        stock_ids = df["證券代號"].astype(str).tolist()
        print(f"[price_fetcher] ✅ 擷取完成，共 {len(stock_ids)} 檔")
        return stock_ids

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return []
