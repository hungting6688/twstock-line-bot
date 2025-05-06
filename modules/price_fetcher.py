print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import requests
import pandas as pd
from io import StringIO

def get_realtime_top_stocks(limit=100) -> list:
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"

    try:
        res = requests.get(url)
        csv_data = res.text

        # 清除不規則前綴行
        cleaned = "\n".join([line for line in csv_data.splitlines() if line.count(",") > 5])
        df = pd.read_csv(StringIO(cleaned))

        # 顯示欄位供除錯用
        print(f"[price_fetcher] 欄位名稱：{df.columns.tolist()}")

        # 嘗試自動偵測成交金額欄位名稱
        turnover_col = next((col for col in df.columns if "成交金額" in col), None)
        if turnover_col is None:
            raise ValueError("找不到成交金額欄位，請確認證交所資料格式是否已變更。")

        # 欄位重新命名
        df = df.rename(columns={"證券代號": "stock_id", turnover_col: "turnover"})
        df["turnover"] = pd.to_numeric(df["turnover"], errors="coerce")
        df = df.dropna(subset=["stock_id", "turnover"])

        # 取成交金額前 N 高的股票代碼
        top_stocks = df.sort_values(by="turnover", ascending=False)["stock_id"].astype(str).head(limit).tolist()
        print(f"[price_fetcher] ✅ 成功取得熱門股前 {limit} 檔")
        return top_stocks

    except Exception as e:
        print(f"[price_fetcher] ❌ 資料解析失敗：{e}")
        return []
