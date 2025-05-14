print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import pandas as pd
import requests
import csv
from io import StringIO
from datetime import datetime

def fetch_price_data(limit=100):
    print("[price_fetcher] ⏳ 擷取台股熱門股清單（來自 TWSE CSV）...")

    today = datetime.now().strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={today}&type=ALL"

    try:
        response = requests.get(url, timeout=10)
        raw_text = response.text

        # 擷取包含「證券代號」的表格開始行
        data_lines = []
        found_header = False
        for line in raw_text.splitlines():
            if "證券代號" in line:
                found_header = True
            if found_header:
                data_lines.append(line)
            if found_header and line.count(",") <= 1:
                break  # 表格結束

        clean_csv = "\n".join(data_lines).strip()
        df = pd.read_csv(StringIO(clean_csv))

        expected = ["證券代號", "證券名稱", "成交股數", "成交金額", "收盤價"]
        df = df[expected].copy()
        df.columns = expected

        df["成交金額"] = (
            df["成交金額"].astype(str).str.replace(",", "", regex=False)
        ).astype(float)

        df = df.sort_values("成交金額", ascending=False).head(limit).reset_index(drop=True)
        print(f"[price_fetcher] ✅ 共取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()
