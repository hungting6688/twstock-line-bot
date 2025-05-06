import requests
import pandas as pd
from datetime import datetime, timedelta
from modules.twse_scraper import get_all_valid_twse_stocks


def get_latest_valid_trading_date():
    today = datetime.now()
    if today.weekday() >= 5:  # 週六日
        offset = today.weekday() - 4
        today -= timedelta(days=offset)
    return today.strftime("%Y-%m-%d")


def get_all_stock_ids(limit=100, filter_type="all"):
    all_stocks = get_all_valid_twse_stocks()  # List of dicts

    df = pd.DataFrame(all_stocks)

    if filter_type == "large_cap":
        df = df[df["type"] == "large"]
    elif filter_type == "small_cap":
        df = df[df["type"] == "small"]

    if limit:
        df = df.sample(n=min(limit, len(df)), random_state=42)

    return df["stock_id"].tolist()


def is_etf(stock_name: str) -> bool:
    etf_keywords = ["ETF", "元大", "富邦", "永豐", "國泰", "中信", "兆豐"]
    return any(keyword in stock_name for keyword in etf_keywords)


def get_all_valid_twse_stocks_with_type():
    raw = get_all_valid_twse_stocks()
    stocks = []
    for item in raw:
        stock_id = item["stock_id"]
        stock_name = item["stock_name"]
        stock_type = "etf" if is_etf(stock_name) else "large" if int(stock_id) < 4000 else "small"
        stocks.append({"stock_id": stock_id, "stock_name": stock_name, "type": stock_type})
    return stocks
