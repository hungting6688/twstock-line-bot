# modules/price_fetcher.py

import pandas as pd
from io import StringIO
import requests
import re

print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

def fetch_price_data(limit=100):
    print("[price_fetcher] ⏳ 擷取台股熱門股清單（來自 TWSE CSV）...")
    
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"
    headers = { "User-Agent": "Mozilla/5.0" }

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        content = resp.content.decode("big5", errors="ignore")

        # 僅保留含「證券代號」開頭的主表資料行
        clean_lines = "\n".join(
            [line for line in content.splitlines() if re.match(r'^\d{4}', line)]
        )
        df = pd.read_csv(StringIO(clean_lines), header=None)

        df.columns = [
            '證券代號', '證券名稱', '成交股數', '成交筆數', '成交金額',
            '開盤價', '最高價', '最低價', '收盤價', '漲跌(+/-)',
            '漲跌價差', '最後揭示買價', '最後揭示買量', '最後揭示賣價',
            '最後揭示賣量', '本益比'
        ][:df.shape[1]]  # 自動對應欄位數

        df['成交金額'] = df['成交金額'].astype(str).str.replace(',', '', regex=False).astype(float)
        df = df.sort_values(by='成交金額', ascending=False).head(limit)

        print(f"[price_fetcher] ✅ 已成功擷取 {len(df)} 檔熱門股")
        return df[['證券代號', '證券名稱', '成交金額', '收盤價']].reset_index(drop=True)

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()
