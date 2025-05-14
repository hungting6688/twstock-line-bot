print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import pandas as pd
import requests
from io import StringIO
import re

def fetch_price_data(limit=100):
    print("[price_fetcher] ⏳ 擷取台股熱門股清單（來自 TWSE CSV）...")
    url = "https://www.twse.com.tw/zh/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"

    try:
        response = requests.get(url, timeout=10)
        response.encoding = "big5"
        raw_text = response.text

        # 僅保留含「成交股數」欄位的主表格區段
        lines = [line for line in raw_text.split("\n") if "成交股數" in line or re.match(r'^\d{4}', line)]
        cleaned_csv = "\n".join(lines)

        df = pd.read_csv(StringIO(cleaned_csv))
        df.columns = df.columns.str.strip()
        print(f"[price_fetcher] 取得欄位名稱：{df.columns.tolist()}")

        required_cols = ["證券代號", "證券名稱", "成交金額"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"缺少欄位：{col}，實際欄位：{df.columns.tolist()}")

        df = df[required_cols].copy()
        df["成交金額"] = df["成交金額"].replace(",", "", regex=True).astype(float)
        df = df.sort_values("成交金額", ascending=False).head(limit)

        df = df.rename(columns={"證券代號": "stock_id", "證券名稱": "name"})
        df.reset_index(drop=True, inplace=True)

        print(f"[price_fetcher] ✅ 成功取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()
