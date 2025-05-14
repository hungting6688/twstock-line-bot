# modules/price_fetcher.py
print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股 with price info)")

import pandas as pd
import requests
from io import StringIO

def fetch_price_data(limit=100, include_etf=False):
    print("[price_fetcher] ⏳ 擷取台股熱門股清單（來自 TWSE CSV）...")

    try:
        url = "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX_ALL?response=csv&date=&selectType=ALL"
        headers = { "User-Agent": "Mozilla/5.0" }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "utf-8"

        # 找表頭起始行
        lines = resp.text.splitlines()
        start_idx = None
        for idx, line in enumerate(lines):
            if line.replace(" ", "").startswith('"證券代號","證券名稱"'):
                start_idx = idx
                break

        if start_idx is None:
            raise ValueError("❌ 找不到正確欄位開頭")

        csv_text = "\n".join(lines[start_idx:])
        df = pd.read_csv(StringIO(csv_text))

        # 檢查必要欄位
        expected_cols = ["證券代號", "證券名稱", "成交股數", "成交金額", "開盤價", "最高價", "最低價", "收盤價"]
        for col in expected_cols:
            if col not in df.columns:
                raise ValueError("❌ 缺少欄位：" + col)

        # 數值欄位清理
        for col in ["成交金額", "成交股數", "開盤價", "最高價", "最低價", "收盤價"]:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "", regex=False), errors="coerce")

        df = df[df["成交金額"] > 0]  # 有成交
        df = df[~df["證券代號"].astype(str).str.contains("^[a-zA-Z]+", regex=True)]  # 排除權證/特別項

        if not include_etf:
            df = df[~df["證券名稱"].str.contains("ETF|ETN|基金", na=False)]

        df = df.sort_values("成交金額", ascending=False).head(limit)

        df = df.rename(columns={
            "證券代號": "stock_id",
            "證券名稱": "name",
            "成交金額": "turnover",
            "成交股數": "volume",
            "開盤價": "open",
            "最高價": "high",
            "最低價": "low",
            "收盤價": "close"
        })

        print(f"[price_fetcher] ✅ 共取得 {len(df)} 檔熱門股")
        return df[["stock_id", "name", "volume", "turnover", "open", "high", "low", "close"]]

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()
