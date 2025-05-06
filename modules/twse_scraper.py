# modules/twse_scraper.py

import requests
import pandas as pd
from io import StringIO

def get_all_valid_twse_stocks():
    url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.encoding = 'big5'

    tables = pd.read_html(StringIO(response.text))
    df = tables[0]
    df.columns = df.iloc[0]
    df = df[1:]

    all_stocks = []
    for _, row in df.iterrows():
        if pd.isna(row["有價證券代號及名稱"]):
            continue
        parts = str(row["有價證券代號及名稱"]).split()
        if len(parts) != 2:
            continue
        stock_id, stock_name = parts
        market_type = str(row["市場別"])
        industry = str(row["產業別"])

        # 篩選上市股票，排除下市、空白代碼
        if not stock_id.isdigit():
            continue

        # 排除已下市或特別標記的股票
        if "下市" in stock_name:
            continue

        all_stocks.append({
            "stock_id": stock_id,
            "stock_name": stock_name,
            "market_type": market_type,
            "industry": industry
        })

    return all_stocks
