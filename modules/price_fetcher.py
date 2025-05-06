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

        # 只保留包含「證券代號」開頭的表格資料段落
        lines = csv_data.split("\n")
        start_idx = None
        for i, line in enumerate(lines):
            if "證券代號" in line:
                start_idx = i
                break
        if start_idx is None:
            raise ValueError("未找到表格標題")

        cleaned_csv = "\n".join(lines[start_idx:])
        df = pd.read_csv(StringIO(cleaned_csv), engine="python")
        df.columns = df.columns.str.strip()
        df = df.rename(columns={"證券代號": "stock_id", "成交金額(千元)": "turnover"})

        df = df[["stock_id", "turnover"]].dropna()
        df["turnover"] = pd.to_numeric(df["turnover"].astype(str).str.replace(",", ""), errors="coerce")
        df = df.dropna(subset=["turnover"])
        df = df.sort_values(by="turnover", ascending=False)
        return df["stock_id"].astype(str).str.zfill(4).head(limit).tolist()

    except Exception as e:
        print(f"[price_fetcher] ❌ 資料解析失敗：{e}")
        return []

# 兼容性別名
get_top_stocks = get_realtime_top_stocks