# modules/price_fetcher.py
print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import pandas as pd
import requests
from io import StringIO

def fetch_price_data():
    print("[price_fetcher] ⏳ 擷取台股熱門股清單（來自 TWSE CSV）...")

    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"
    try:
        resp = requests.get(url, timeout=10)
        raw_text = resp.text

        # 尋找正確開頭
        lines = raw_text.splitlines()
        start_idx = -1
        for i, line in enumerate(lines):
            if line.startswith('證券代號') or line.startswith('"證券代號'):
                start_idx = i
                break

        if start_idx == -1:
            raise ValueError("❌ 找不到正確欄位開頭")

        # 篩選有效內容區塊
        csv_content = "\n".join(lines[start_idx:])
        df = pd.read_csv(StringIO(csv_content), encoding="big5")

        # 重新命名常用欄位
        df.columns = [col.strip() for col in df.columns]
        df = df.rename(columns={
            df.columns[0]: "證券代號",
            df.columns[1]: "證券名稱",
            df.columns[2]: "成交股數",
            df.columns[8]: "收盤價",
            df.columns[4]: "成交金額"
        })

        df = df[["證券代號", "證券名稱", "成交股數", "成交金額", "收盤價"]]
        df = df.dropna()

        # 清理數值欄位格式
        for col in ["成交股數", "成交金額", "收盤價"]:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace('--', '0', regex=False)
                .astype(float)
            )

        df = df[df["收盤價"] > 0]
        df = df.sort_values("成交金額", ascending=False)
        df["證券代號"] = df["證券代號"].astype(str).str.zfill(4)

        print(f"[price_fetcher] ✅ 共取得 {len(df)} 檔熱門股")
        return df.reset_index(drop=True)

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()
