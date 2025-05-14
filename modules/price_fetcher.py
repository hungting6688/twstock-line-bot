# modules/price_fetcher.py
print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import pandas as pd
import requests
from io import StringIO

def fetch_price_data(limit=None):
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"

    try:
        response = requests.get(url)
        csv_text = response.text
        lines = [line for line in csv_text.splitlines() if len(line.split('",')) > 10]
        csv_cleaned = "\n".join(lines)
        df = pd.read_csv(StringIO(csv_cleaned))
    except Exception as e:
        print(f"[price_fetcher] ❌ 無法下載或解析資料：{e}")
        return pd.DataFrame()

    # 清理欄位名稱與數據格式
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "證券代號": "證券代號",
        "證券名稱": "證券名稱",
        "成交股數": "成交股數",
        "成交金額": "成交金額",
    })

    for col in ["成交股數", "成交金額"]:
        df[col] = df[col].astype(str).str.replace(",", "").str.replace("--", "0")
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["成交金額"] = df["成交金額"] * 1000  # 單位為千元

    # 篩選每日成交金額前幾大的股票
    df = df[df["成交金額"] > 0].sort_values("成交金額", ascending=False)
    if limit:
        df = df.head(limit)

    return df.reset_index(drop=True)
