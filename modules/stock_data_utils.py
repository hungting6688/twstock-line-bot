import datetime
import requests
import pandas as pd
import gspread
import os
import json
from oauth2client.service_account import ServiceAccountCredentials

def get_latest_valid_trading_date():
    today = datetime.date.today()
    delta = datetime.timedelta(days=1)
    for i in range(7):  # 最多往前找一週
        date = today - delta * i
        if date.weekday() < 5:  # 0=Monday, 6=Sunday
            return date.strftime("%Y-%m-%d")
    return today.strftime("%Y-%m-%d")

def get_all_stock_ids(limit=100, filter_type="all", include_etf=True):
    from modules.twse_scraper import get_all_valid_twse_stocks

    all_stocks = get_all_valid_twse_stocks()
    if not include_etf:
        all_stocks = all_stocks[~all_stocks["證券名稱"].str.contains("ETF")]

    if filter_type == "large_cap":
        stocks = all_stocks.head(limit)
    elif filter_type == "small_cap":
        stocks = all_stocks.tail(limit)
    else:
        stocks = all_stocks.sample(n=limit, random_state=42) if limit else all_stocks

    return stocks["證券代號"].tolist()

def get_tracking_stock_ids(sheet_name="追蹤清單", col=1):
    """
    從 Google Sheets 讀取 A 欄的自選追蹤股票代碼，排除第一列標題。
    """
    json_key = json.loads(os.environ["GOOGLE_JSON_KEY"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(json_key, scope)
    gc = gspread.authorize(credentials)
    
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    sh = gc.open_by_key(sheet_id)
    worksheet = sh.worksheet(sheet_name)

    stock_ids = worksheet.col_values(col)[1:]  # 跳過第一列標題
    stock_ids = [s.strip() for s in stock_ids if s.strip() != ""]
    return stock_ids
