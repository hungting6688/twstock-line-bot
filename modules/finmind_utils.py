import requests
import os
from datetime import datetime

FINMIND_API_URL = "https://api.finmindtrade.com/api/v4/data"
FINMIND_TOKEN = os.environ.get("FINMIND_TOKEN")  # 由 GitHub Secrets 提供

def get_intraday_breakout_stocks(limit=5):
    today = datetime.now().strftime("%Y-%m-%d")
    payload = {
        "dataset": "TaiwanStockPrice",
        "start_date": today,
        "data_id": "2330",  # TODO: 換成多檔熱門股處理
        "token": FINMIND_TOKEN,
    }
    # 範例回傳假資料，請用真實邏輯替換
    return [("2330", "成交量放大，短線轉強"), ("2615", "多頭動能轉強")][:limit]

def get_top_dividend_stocks(limit=5):
    payload = {
        "dataset": "TaiwanStockDividend",
        "data_id": "2330",
        "token": FINMIND_TOKEN
    }
    # 範例，應使用預估殖利率排序
    return [("2884", 6.2), ("2609", 5.8), ("1101", 5.5)][:limit]

def get_closing_recommendations(limit=5):
    # 可整合法人、技術分析、追蹤股
    return [
        ("3035", "法人買超 + 技術轉強"),
        ("6488", "多日強勢 + 量能配合"),
        ("2368", "追蹤股表現佳")
    ][:limit]
