# modules/price_fetcher.py
print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import pandas as pd
import requests
from io import StringIO
from datetime import datetime

def fetch_price_data(limit=100):
    print("[price_fetcher] ⏳ 擷取台股熱門股清單（來自 TWSE CSV）...")

    url = "https://www.twse.com.tw/zh/page/trading/exchange/MI_INDEX.html"
    today = datetime.today().strftime("%Y%m%d")
    csv_url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={today}&type=ALL"

    try:
        response = requests.get(csv_url, timeout=10)
        response.encoding = "utf-8"
        raw_text = response.text

        # 過濾掉非數據列（通常是欄位列以上的文字或總計列）
        lines = [line for line in raw_text.splitlines() if line.count('",') >= 10]
        cleaned = "\n".join(lines)
        df = pd.read_csv(StringIO(cleaned))

        # 欄位重新命名（保險起見）
        df.columns = [col.strip().replace('"', '') for col in df.columns]

        # 過濾欄位並新增成交金額（單位：元）
        df = df[["證券代號", "證券名稱", "成交股數", "成交金額", "收盤價"]].copy()
        df = df.dropna(subset=["成交金額", "成交股數"])

        df["成交金額"] = df["成交金額"].astype(str).str.replace(",", "").astype(float) * 1000
        df = df.sort_values("成交金額", ascending=False).head(limit).reset_index(drop=True)

        print(f"[price_fetcher] ✅ 共取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{str(e)}")
        return pd.DataFrame()