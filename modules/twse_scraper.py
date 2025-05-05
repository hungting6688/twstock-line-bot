import requests
import pandas as pd


def get_all_valid_twse_stocks():
    url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    tables = pd.read_html(response.text)

    df = tables[0]
    df.columns = df.iloc[0]
    df = df[1:]
    df = df.rename(columns={"有價證券代號及名稱": "stock_info"})

    valid_stocks = []
    for _, row in df.iterrows():
        stock_info = row["stock_info"]
        if not isinstance(stock_info, str) or len(stock_info.strip()) < 4:
            continue
        if "　" not in stock_info:
            continue

        stock_id, stock_name = stock_info.split("　", 1)
        market = row.get("市場別", "")
        industry = row.get("產業別", "")
        type_ = "stock"
        if "ETF" in industry or "ETF" in stock_name:
            type_ = "etf"

        valid_stocks.append({
            "stock_id": stock_id.strip(),
            "stock_name": stock_name.strip(),
            "market": market.strip(),
            "industry_category": industry.strip(),
            "type": type_,
            "is_valid": True
        })

    return valid_stocks
