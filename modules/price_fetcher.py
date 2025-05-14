# modules/price_fetcher.py

import requests
import pandas as pd
from io import StringIO

print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

def fetch_price_data(limit=100):
    print("[price_fetcher] ⏳ 擷取台股熱門股清單（來自 TWSE CSV）...")

    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"
    headers = { "User-Agent": "Mozilla/5.0" }

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        content = resp.content.decode("big5", errors="ignore")

        # 只保留包含「證券代號」欄位的資料表
        lines = content.splitlines()
        data_lines = [line for line in lines if line.strip().startswith("證券代號")]
        if not data_lines:
            raise ValueError("❌ 找不到正確欄位開頭")

        start_index = lines.index(data_lines[0])
        csv_data = "\n".join(lines[start_index:])

        df = pd.read_csv(StringIO(csv_data))

        required_columns = ['證券代號', '證券名稱', '成交金額', '收盤價']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"❌ 缺少必要欄位，請檢查 TWSE 原始格式\n[price_fetcher] 欄位名稱： {df.columns.tolist()}")

        df = df[required_columns].copy()
        df['成交金額'] = df['成交金額'].astype(str).str.replace(',', '', regex=False).astype(float)
        df = df.sort_values(by='成交金額', ascending=False).head(limit)
        df = df.reset_index(drop=True)

        print(f"[price_fetcher] ✅ 已成功擷取 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()
