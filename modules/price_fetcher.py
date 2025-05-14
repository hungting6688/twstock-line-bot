# modules/price_fetcher.py
print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import pandas as pd
import requests
from io import StringIO
from datetime import datetime

def fetch_price_data(limit=100):
    url = "https://www.twse.com.tw/zh/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"  # 即時成交資訊
    response = requests.get(url)
    content = response.text

    lines = [line for line in content.split('\n') if line.count(',') > 10]
    csv_data = '\n'.join(lines)
    df = pd.read_csv(StringIO(csv_data))

    df = df.rename(columns=lambda x: x.strip())
    df = df.rename(columns={"資訊代號": "證券代號", "資訊名稱": "證券名稱"})

    df["證券代號"] = df["\u8b49\u5238\u4ee3\u865f"].astype(str)
    df["\u8b49\u5238\u4ee3\u865f"] = df["\u8b49\u5238\u4ee3\u865f"].str.replace('=\"', '').str.replace('\"', '').str.strip()

    df = df[df["\u6210\u4ea4\u91d1\u984d"].apply(lambda x: str(x).replace(",", "").isdigit())]
    df["\u6210\u4ea4\u91d1\u984d"] = df["\u6210\u4ea4\u91d1\u984d"].astype(str).str.replace(",", "").astype(float)

    df = df.sort_values("\u6210\u4ea4\u91d1\u984d", ascending=False)
    df = df.head(limit).reset_index(drop=True)

    return df
