# modules/stock_data_utils.py

import os
import datetime
import pytz
import gspread
import json
import requests
from oauth2client.service_account import ServiceAccountCredentials

# ✅ 取得最近有效交易日
def get_latest_valid_trading_date():
    tz = pytz.timezone("Asia/Taipei")
    now = datetime.datetime.now(tz)
    today = now.date()

    if now.hour < 15:
        today -= datetime.timedelta(days=1)

    while today.weekday() >= 5:
        today -= datetime.timedelta(days=1)

    return today.strftime("%Y-%m-%d")

# ✅ 從 Google Sheet 擷取額外股票代碼
def get_google_sheet_stock_ids():
    try:
        sheet_key = os.environ.get("GOOGLE_SHEET_ID")
        json_key = os.environ.get("GOOGLE_JSON_KEY")
        creds_dict = json.loads(json_key)

        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_key)
        worksheet = sheet.get_worksheet(0)

        records = worksheet.col_values(1)[1:]  # 忽略標題列
        stock_ids = [r.strip() for r in records if r.strip()]
        return stock_ids
    except Exception as e:
        print(f"⚠️ 無法讀取 Google Sheets：{e}")
        return []

# ✅ 自動爬取所有上市櫃股票（含 ETF）
def get_all_stock_ids(limit=9999, filter_type="all"):
    try:
        url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.encoding = "big5"
        lines = response.text.split("\n")
        stock_ids = []

        for line in lines:
            if "上市" in line and "股票" in line:
                parts = line.split("\t")
                if len(parts) > 1:
                    code_name = parts[0].strip()
                    if code_name and code_name[:4].isdigit():
                        stock_id = code_name[:4]
                        stock_ids.append(stock_id)

        # 選擇性過濾（目前保留 ETF）
        # 篩選類型
        if filter_type == "small_cap":
            stock_ids = [sid for sid in stock_ids if sid.startswith(("3", "4", "6"))]
        elif filter_type == "large_cap":
            stock_ids = [sid for sid in stock_ids if sid.startswith(("1", "2"))]

        # 加入 Google Sheet 額外追蹤股
        sheet_ids = get_google_sheet_stock_ids()
        for sid in sheet_ids:
            if sid not in stock_ids:
                stock_ids.append(sid)

        return stock_ids[:limit]
    except Exception as e:
        print(f"⚠️ 抓取股票代碼失敗：{e}")
        return []
