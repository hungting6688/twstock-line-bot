print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import requests
import pandas as pd
from io import StringIO

def get_realtime_top_stocks(min_turnover=5e7):
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"
    try:
        response = requests.get(url)
        raw_text = response.text
        # 清理非標準 CSV 格式行
        cleaned = "\n".join([line for line in raw_text.split("\n") if len(line.split(",")) > 10])
        df = pd.read_csv(StringIO(cleaned))

        df.columns = df.columns.str.strip()
        df = df.rename(columns={
            '證券代號': 'stock_id',
            '成交股數': 'volume',
            '成交金額': 'value',
            '收盤價': 'close'
        })

        df["stock_id"] = df["stock_id"].astype(str).str.zfill(4)
        df["volume"] = pd.to_numeric(df["volume"].astype(str).str.replace(",", ""), errors="coerce")
        df["close"] = pd.to_numeric(df["close"].astype(str).str.replace(",", ""), errors="coerce")
        df["turnover"] = df["volume"] * df["close"]

        df = df.dropna(subset=["turnover"])
        filtered_df = df[df["turnover"] > min_turnover]

        top_stocks = filtered_df.sort_values("turnover", ascending=False)["stock_id"].tolist()
        print(f"[price_fetcher] ✅ 成功取得熱門股數量：{len(top_stocks)}")
        return top_stocks
    except Exception as e:
        print(f"[price_fetcher] ❌ 資料解析失敗：{e}")
        return []