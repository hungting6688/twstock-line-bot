import requests
import os
from datetime import datetime, timedelta

FINMIND_TOKEN = os.getenv("FINMIND_TOKEN")

def get_today_date():
    return datetime.today().strftime("%Y-%m-%d")

def get_top_dividend_stocks(limit=5):
    url = "https://api.finmindtrade.com/api/v4/data"
    payload = {
        "dataset": "TaiwanStockDividend",
        "data_id": "",
        "start_date": "2024-01-01",
        "token": FINMIND_TOKEN
    }
    r = requests.get(url, params=payload)
    data = r.json()["data"]

    latest = sorted(data, key=lambda x: x.get("cash_dividend", 0), reverse=True)
    result = [(d["stock_id"], round(d.get("cash_dividend", 0), 2)) for d in latest if d.get("cash_dividend", 0) > 0]
    return result[:limit]

def get_intraday_breakout_stocks(limit=5):
    # 模擬方法：找前日成交量大增股票（未來可替換為即時價量異常判斷）
    url = "https://api.finmindtrade.com/api/v4/data"
    yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    payload = {
        "dataset": "TaiwanStockPrice",
        "start_date": yesterday,
        "token": FINMIND_TOKEN
    }
    r = requests.get(url, params=payload)
    data = r.json()["data"]

    # 找出近一天成交量前幾高個股
    volume_ranking = {}
    for item in data:
        stock_id = item["stock_id"]
        volume_ranking.setdefault(stock_id, 0)
        volume_ranking[stock_id] += item["Trading_Volume"]

    sorted_volume = sorted(volume_ranking.items(), key=lambda x: x[1], reverse=True)
    return [(stock_id, "成交量異常放大") for stock_id, _ in sorted_volume[:limit]]

def get_closing_recommendations(limit=5):
    # 模擬綜合：法人買超、量能、技術整合（可替換為複合評分模型）
    url = "https://api.finmindtrade.com/api/v4/data"
    payload = {
        "dataset": "TaiwanStockInstitutionalInvestorsBuySell",
        "start_date": get_today_date(),
        "token": FINMIND_TOKEN
    }
    r = requests.get(url, params=payload)
    data = r.json()["data"]

    net_buy = {}
    for d in data:
        sid = d["stock_id"]
        net_buy.setdefault(sid, 0)
        net_buy[sid] += d["buy"] - d["sell"]

    top_picks = sorted(net_buy.items(), key=lambda x: x[1], reverse=True)
    return [(sid, "法人買超強勁，表現可期") for sid, val in top_picks[:limit]]
