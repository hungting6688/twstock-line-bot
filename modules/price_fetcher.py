# modules/price_fetcher.py
print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import pandas as pd
import requests
from io import StringIO
from datetime import datetime

def fetch_price_data(limit=100):
    print("[price_fetcher] ⏳ 擷取台股熱門股清單（來自 TWSE CSV）...")

    today = datetime.today().strftime("%Y%m%d")
    csv_url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={today}&type=ALL"

    try:
        response = requests.get(csv_url, timeout=10)
        response.encoding = "utf-8"
        raw_text = response.text

        # 清理 CSV，只保留包含逗號多的資料列
        lines = [line for line in raw_text.splitlines() if line.count('",') >= 10]
        cleaned = "\n".join(lines)
        df = pd.read_csv(StringIO(cleaned))

        # 印出實際欄位確認
        print("[price_fetcher] 欄位名稱：", df.columns.tolist())

        # 重新命名欄位、轉換欄位名稱
        df.columns = [col.strip().replace('"', '') for col in df.columns]
        df = df.rename(columns=lambda x: x.strip())

        expected_cols = ["證券代號", "證券名稱", "成交股數", "成交金額", "收盤價"]
        if not all(col in df.columns for col in expected_cols):
            raise ValueError("❌ 缺少必要欄位，請檢查 TWSE 原始格式")

        df = df[expected_cols].copy()
        df = df.dropna(subset=["成交金額", "成交股數"])

        # 轉數字
        df["成交金額"] = df["成交金額"].astype(str).str.replace(",", "").astype(float) * 1000
        df = df.sort_values("成交金額", ascending=False).head(limit).reset_index(drop=True)

        print(f"[price_fetcher] ✅ 共取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{str(e)}")
        return pd.DataFrame()
