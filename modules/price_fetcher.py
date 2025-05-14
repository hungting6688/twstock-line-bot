print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import pandas as pd
import requests
from io import StringIO
from datetime import datetime

def fetch_price_data(limit=100):
    print("[price_fetcher] ⏳ 擷取台股熱門股清單（來自 TWSE CSV）...")

    today = datetime.now().strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={today}&type=ALL"

    try:
        response = requests.get(url, timeout=10)
        csv_text = response.text

        # 清理 CSV 字串：移除空行與亂碼
        lines = csv_text.split("\n")
        clean_lines = [line.strip() for line in lines if line.strip() and len(line.split(",")) > 10]
        clean_csv = "\n".join(clean_lines)

        df = pd.read_csv(StringIO(clean_csv))

        expected_columns = ['證券代號', '證券名稱', '成交股數', '成交金額', '收盤價']
        if not all(col in df.columns for col in expected_columns):
            print(f"[price_fetcher] ❌ 擷取失敗：缺少必要欄位 {expected_columns}")
            return pd.DataFrame()

        df = df[expected_columns].copy()
        df.columns = ["證券代號", "證券名稱", "成交股數", "成交金額", "收盤價"]

        # 數值清洗
        df["成交金額"] = (
            df["成交金額"].astype(str).str.replace(",", "", regex=False)
        ).astype(float)

        # 排序 + 限制數量
        df = df.sort_values("成交金額", ascending=False).head(limit).reset_index(drop=True)
        print(f"[price_fetcher] ✅ 共取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()
