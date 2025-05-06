# modules/price_fetcher.py
print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import pandas as pd
import requests
from io import StringIO

def get_realtime_top_stocks(limit: int = 100) -> list:
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"
    try:
        response = requests.get(url)
        response.encoding = "big5"
        csv_data = response.text

        # 加入錯誤容忍機制，略過異常行
        df = pd.read_csv(StringIO(csv_data), on_bad_lines="skip")

        df.columns = df.columns.str.strip()
        df = df.rename(columns=lambda x: str(x).strip())
        df = df.rename(columns={"證券代號": "stock_id", "成交金額(千元)": "turnover"})

        # 移除非數字的行與 NaN
        df = df[pd.to_numeric(df["turnover"], errors="coerce").notnull()]
        df["turnover"] = df["turnover"].str.replace(",", "").astype(float)

        # 篩選成交金額 > 5,000 萬的熱門股
        df = df[df["turnover"] > 50000]
        top_stocks = df["stock_id"].astype(str).str.zfill(4).tolist()
        return top_stocks[:limit]

    except Exception as e:
        print(f"[price_fetcher] ❌ 資料解析失敗：{e}")
        return []
