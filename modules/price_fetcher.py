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

        # 找到包含必要欄位的資料區段（以證券代號、證券名稱開頭）
        lines = content.splitlines()
        useful_lines = []
        recording = False
        for line in lines:
            if '證券代號' in line and '證券名稱' in line:
                recording = True
                useful_lines.append(line)
            elif recording:
                if line.strip() == "":
                    break
                useful_lines.append(line)

        if not useful_lines:
            raise ValueError("❌ 找不到正確欄位資料段")

        df = pd.read_csv(StringIO("\n".join(useful_lines)))

        required = ['證券代號', '證券名稱', '成交金額', '收盤價']
        if not all(col in df.columns for col in required):
            raise ValueError(f"❌ 缺少必要欄位，實際欄位為：{df.columns.tolist()}")

        df['成交金額'] = df['成交金額'].astype(str).str.replace(",", "", regex=False).astype(float)
        df = df.sort_values(by='成交金額', ascending=False).head(limit).reset_index(drop=True)

        print(f"[price_fetcher] ✅ 已成功擷取 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()
