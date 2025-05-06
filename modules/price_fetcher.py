# modules/price_fetcher.py
print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import pandas as pd
import requests
from io import StringIO

def get_realtime_top_stocks(limit: int = 100) -> list:
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"

    try:
        response = requests.get(url, timeout=10)
        response.encoding = "big5"
        raw_data = response.text

        # 過濾出包含有效股票代號的行（例如開頭為數字）
        lines = raw_data.splitlines()
        valid_rows = [line for line in lines if line.strip() and line.strip()[0].isdigit()]
        cleaned_data = "\n".join(valid_rows)

        df = pd.read_csv(StringIO(cleaned_data), header=None)

        # 避免欄位數錯誤，強制取前幾欄
        df = df.iloc[:, :9]
        df.columns = ["stock_id", "name", "成交股數", "成交金額", "成交筆數", "開盤價", "最高價", "最低價", "收盤價"]

        df["成交金額"] = df["成交金額"].str.replace(",", "", regex=False)
        df["turnover"] = pd.to_numeric(df["成交金額"], errors="coerce")
        df = df.dropna(subset=["stock_id", "turnover"])

        # 僅保留成交金額大於五千萬的股票
        df = df[df["turnover"] > 50000]
        df["stock_id"] = df["stock_id"].astype(str).str.zfill(4)

        top_stocks = df["stock_id"].tolist()
        return top_stocks[:limit]

    except Exception as e:
        print(f"[price_fetcher] ❌ 資料解析失敗：{e}")
        return []
