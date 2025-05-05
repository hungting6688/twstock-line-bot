import os
import requests
import pandas as pd
import random
from datetime import datetime, timedelta
from modules.twse_scraper import get_all_valid_twse_stocks


def get_latest_valid_trading_date():
    today = datetime.today()
    delta = timedelta(days=1)
    for _ in range(7):  # 最多往前找七天
        if today.weekday() < 5:  # 0~4 為週一到週五
            return today.strftime("%Y-%m-%d")
        today -= delta
    return today.strftime("%Y-%m-%d")


def get_all_stock_ids(limit=100, filter_type="all"):
    all_stocks = get_all_valid_twse_stocks()

    # 篩選條件：排除已下市、保留 ETF
    all_stocks = [s for s in all_stocks if s["is_valid"] and (s["type"] in ["stock", "etf"])]

    # 進一步分類
    if filter_type == "large_cap":
        filtered = [s for s in all_stocks if s["market"] == "上市" and s["industry_category"] not in ["ETF", "受益證券"]]
    elif filter_type == "small_cap":
        filtered = [s for s in all_stocks if s["market"] == "上櫃" and s["industry_category"] not in ["ETF", "受益證券"]]
    else:
        filtered = all_stocks

    # 隨機選取 limit 檔（若有設定）
    stocks = random.sample(filtered, k=limit) if limit else filtered
    return [s["stock_id"] for s in stocks]


def get_tracking_stock_ids():
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    import json

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    json_key = json.loads(os.environ["GOOGLE_JSON_KEY"])
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(json_key, scope)
    gc = gspread.authorize(credentials)

    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    sh = gc.open_by_key(sheet_id)
    worksheet = sh.get_worksheet(0)  # 第一個工作表

    data = worksheet.col_values(1)  # 讀取第一欄
    return [stock_id.strip() for stock_id in data[1:] if stock_id.strip()]  # 排除標題與空白
