import os
import requests
from datetime import datetime, timedelta

def get_latest_valid_trading_date():
    """取得最近一個有效交易日，假日自動往前回退。"""
    today = datetime.today()
    for i in range(7):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        if is_trading_day(date):
            return date
    raise ValueError("找不到有效交易日")

def is_trading_day(date):
    """檢查某日是否為台股交易日。"""
    url = "https://api.finmindtrade.com/api/v4/data"
    token = os.environ.get("FINMIND_TOKEN")
    payload = {
        "dataset": "TaiwanStockInfo",
        "token": token
    }
    resp = requests.get(url, params=payload)
    return date <= datetime.today().strftime("%Y-%m-%d")

def fetch_finmind_data(stock_id, start_date, end_date):
    url = "https://api.finmindtrade.com/api/v4/data"
    token = os.environ.get("FINMIND_TOKEN")
    payload = {
        "dataset": "TaiwanStockTechnicalIndicator",
        "data_id": stock_id,
        "start_date": start_date,
        "end_date": end_date,
        "token": token
    }
    resp = requests.get(url, params=payload)
    data = resp.json().get("data", [])
    if not data:
        print(f"⚠️ FinMind 無資料：{stock_id}")
        return None
    return pd.DataFrame(data)

def get_hot_stock_ids(limit=100, filter_type="all"):
    """取得 FinMind 熱門前 N 檔股票，可選擇大型/小型股類型"""
    url = "https://api.finmindtrade.com/api/v4/data"
    token = os.environ.get("FINMIND_TOKEN")
    date = get_latest_valid_trading_date()
    payload = {
        "dataset": "TaiwanStockTradingDaily",
        "data_id": "熱門排行",
        "start_date": date,
        "token": token
    }

    resp = requests.get(url, params=payload)
    data = resp.json().get("data", [])
    stock_ids = [d["stock_id"] for d in data][:limit]

    if filter_type == "large_cap":
        return [sid for sid in stock_ids if not sid.startswith("3")]
    elif filter_type == "small_cap":
        return [sid for sid in stock_ids if sid.startswith("3")]
    else:
        return stock_ids
