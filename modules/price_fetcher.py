print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import requests
import pandas as pd
from io import StringIO

def get_realtime_top_stocks(limit=100):
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"
    try:
        response = requests.get(url)
        csv_data = response.text
        dfs = pd.read_csv(StringIO(csv_data), header=None, skiprows=1, thousands=",", engine='python')
        dfs.columns = dfs.iloc[0]
        dfs = dfs[1:]
        dfs = dfs.rename(columns=lambda x: str(x).strip())
        dfs = dfs.rename(columns={"證券代號": "stock_id", "成交金額(千元)": "turnover"})

        dfs["turnover"] = pd.to_numeric(dfs["turnover"], errors="coerce")
        dfs = dfs.dropna(subset=["turnover"])
        dfs = dfs.sort_values(by="turnover", ascending=False)

        top_stocks = dfs["stock_id"].astype(str).str.zfill(4).head(limit).tolist()
        return top_stocks
    except Exception as e:
        print(f"[price_fetcher] ❌ 資料解析失敗：{e}")
        return []

# 給 signal_analysis 相容使用
get_top_stocks = get_realtime_top_stocks