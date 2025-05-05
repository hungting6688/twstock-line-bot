import os
import json
import pandas as pd
from datetime import datetime, timedelta
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

FINMIND_TOKEN = os.getenv("FINMIND_TOKEN")

def get_latest_valid_trading_date():
    today = datetime.now()
    for i in range(5):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInfo&date={date}"
        r = requests.get(url)
        if r.status_code == 200 and r.json().get("data"):
            return date
    return today.strftime("%Y-%m-%d")

def fetch_finmind_data(dataset, params):
    url = f"https://api.finmindtrade.com/api/v4/data"
    params["dataset"] = dataset
    params["token"] = FINMIND_TOKEN
    r = requests.get(url, params=params)
    if r.status_code == 200:
        return pd.DataFrame(r.json()["data"])
    else:
        print(f"⚠️ FinMind API 無資料，請檢查：{dataset} / ***{params}***")
        return None

def fetch_stock_technical_data(stock_id, start_date, end_date):
    df = fetch_finmind_data("TaiwanStockTechnicalIndicator", {
        "stock_id": stock_id,
        "start_date": start_date,
        "end_date": end_date
    })
    if df is not None and not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df

def fetch_financial_statement(stock_id):
    df = fetch_finmind_data("TaiwanStockFinancialStatements", {
        "stock_id": stock_id
    })
    if df is not None and not df.empty:
        df = df[df["type"] == "綜合損益表"]
        df = df[df["column"] == "基本每股盈餘（元）"]
        df = df[df["date"].str.contains("Q4")]  # 取年報 EPS
        df["date"] = pd.to_datetime(df["date"])
        df["EPS"] = df["value"]
        return df[["date", "EPS"]]
    return None

def fetch_institutional_investors(stock_id):
    df = fetch_finmind_data("TaiwanStockInstitutionalInvestors", {
        "stock_id": stock_id,
        "start_date": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
        "end_date": get_latest_valid_trading_date()
    })
    if df is not None and not df.empty:
        df["net_buy"] = df["buy"] - df["sell"]
        return df
    return None

def get_hot_stock_ids(limit=100, filter_type="all"):
    df = fetch_finmind_data("TaiwanStockPrice", {
        "date": get_latest_valid_trading_date()
    })
    if df is None or df.empty or "data" not in df:
        return []

    df = df[df["Trading_Volume"] > 0]
    df = df.groupby("stock_id").agg({"Trading_Volume": "sum"}).reset_index()
    df = df.sort_values(by="Trading_Volume", ascending=False)

    if filter_type == "small_cap":
        df = df[df["stock_id"].str.startswith(("3", "6", "8"))]  # 小型股
    elif filter_type == "large_cap":
        df = df[df["stock_id"].str.startswith(("1", "2"))]  # 大型股

    return df["stock_id"].head(limit).tolist()

def get_tracking_stock_ids():
    try:
        json_key = os.getenv("GOOGLE_JSON_KEY")
        if not json_key:
            return []

        key_dict = json.loads(json_key)
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, scope)
        gc = gspread.authorize(creds)

        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.sheet1
        rows = worksheet.get_all_values()
        stock_ids = [row[0] for row in rows[1:] if row and row[0].isdigit()]
        return stock_ids
    except Exception as e:
        print(f"⚠️ 無法讀取 Google Sheets：{e}")
        return []
