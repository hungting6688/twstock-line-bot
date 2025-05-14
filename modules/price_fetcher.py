# modules/price_fetcher.py
print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import requests
import pandas as pd
from io import StringIO
from datetime import datetime

def fetch_price_data():
    print("[price_fetcher] ⏳ 擷取台股熱門股清單（來自 TWSE CSV）...")

    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX_ALL?response=csv&date={}&type=ALL"
    today_str = datetime.today().strftime("%Y%m%d")
    target_url = url.format(today_str)

    try:
        response = requests.get(target_url, timeout=10)
        raw_text = response.text

        # 找出含有正確欄位的表格起始位置
        lines = raw_text.splitlines()
        header_idx = None
        for i, line in enumerate(lines):
            if "證券代號" in line and "成交金額" in line:
                header_idx = i
                break

        if header_idx is None:
            raise ValueError("❌ 找不到正確欄位開頭")

        content = "\n".join(lines[header_idx:])
        df = pd.read_csv(StringIO(content))

        # 正規化欄位名稱與過濾必要資料
        df.columns = df.columns.str.strip()
        df = df.rename(columns={
            "證券代號": "證券代號",
            "證券名稱": "證券名稱",
            "成交金額": "成交金額",
            "收盤價": "收盤價"
        })

        df["成交金額"] = pd.to_numeric(df["成交金額"].astype(str).str.replace(",", ""), errors="coerce")
        df["收盤價"] = pd.to_numeric(df["收盤價"].astype(str).str.replace(",", ""), errors="coerce")

        df = df.dropna(subset=["成交金額", "收盤價"])
        df = df[["證券代號", "證券名稱", "成交金額", "收盤價"]]

        print(f"[price_fetcher] ✅ 擷取完成，共 {len(df)} 檔")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()
