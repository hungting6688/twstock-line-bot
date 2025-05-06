# modules/price_fetcher.py
print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import requests
import pandas as pd
from io import StringIO

def get_realtime_top_stocks(limit=100):
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"
    try:
        response = requests.get(url)
        csv_data = response.text

        # 移除表頭無效行與欄位逗號不足的雜訊行
        cleaned_lines = []
        for line in csv_data.split("\n"):
            if len(line.strip()) == 0 or line.count(",") < 5:
                continue
            cleaned_lines.append(line)
        cleaned_csv = "\n".join(cleaned_lines)

        df = pd.read_csv(StringIO(cleaned_csv), engine="python")
        df.columns = df.columns.str.strip()
        df = df.rename(columns=lambda x: x.strip())

        # 過濾出主板股票資料欄位
        df = df.rename(columns={"證券代號": "stock_id", "成交金額(千元)": "turnover"})
        df = df[["stock_id", "turnover"]].dropna()
        df["turnover"] = pd.to_numeric(df["turnover"], errors="coerce")
        df = df.dropna(subset=["turnover"])
        df = df.sort_values(by="turnover", ascending=False)
        return df["stock_id"].astype(str).str.zfill(4).head(limit).tolist()

    except Exception as e:
        print(f"[price_fetcher] ❌ 資料解析失敗：{e}")
        return []

# 為兼容舊版 signal_analysis
get_top_stocks = get_realtime_top_stocks