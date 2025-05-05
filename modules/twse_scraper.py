# modules/twse_scraper.py

import requests
import pandas as pd

def get_all_valid_twse_stocks():
    url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    tables = pd.read_html(response.text)

    if not tables:
        return []

    df = tables[0]
    df.columns = df.iloc[0]
    df = df[1:]
    df = df[df["有價證券代號及名稱"].notna()]
    df = df[~df["有價證券代號及名稱"].str.contains("　")]  # 排除無代號類別（如指數、備註）

    stock_list = []
    for _, row in df.iterrows():
        try:
            code_name = row["有價證券代號及名稱"]
            code, name = code_name[:4], code_name[4:].strip()
            if code.isdigit():
                stock_list.append({
                    "股票代號": code,
                    "股票名稱": name,
                    "市值(億元)": estimate_market_cap(row["發行股數(千股)"])
                })
        except Exception:
            continue

    return stock_list

def estimate_market_cap(issued_shares):
    try:
        shares = float(str(issued_shares).replace(",", ""))
        return round(shares * 50 / 10000, 2)  # 假設平均股價為 50 元估算
    except:
        return 0
