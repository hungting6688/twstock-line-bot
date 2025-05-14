print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import pandas as pd
import requests
from io import StringIO

def fetch_price_data(limit=100):
    print("[price_fetcher] ⏳ 擷取台股熱門股清單（來自 TWSE CSV）...")
    url = "https://www.twse.com.tw/zh/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"
    try:
        response = requests.get(url, timeout=10)
        response.encoding = "big5"  # TWSE 網頁用 Big5 編碼
        raw_text = response.text

        # 只保留含有 "成交股數" 欄位的表格資料（排除標題與說明文字）
        lines = [line for line in raw_text.split("\n") if "成交股數" in line or re.match(r'^\d{4}', line)]
        cleaned_csv = "\n".join(lines)

        df = pd.read_csv(StringIO(cleaned_csv))
        df = df.rename(columns=lambda x: x.strip())  # 移除欄位名稱空格
        df = df[["證券代號", "證券名稱", "成交金額"]].copy()

        # 成交金額轉數值
        df["成交金額"] = df["成交金額"].replace(",", "", regex=True).astype(float)
        df = df.sort_values("成交金額", ascending=False).head(limit)

        df = df.rename(columns={"證券代號": "stock_id", "證券名稱": "name"})
        df.reset_index(drop=True, inplace=True)
        print(f"[price_fetcher] ✅ 成功取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()
