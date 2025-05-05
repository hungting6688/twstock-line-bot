# modules/stock_data_utils.py

import os
import datetime
import pytz
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

# ========== ✅ 取得最近有效交易日（含保險機制） ==========
def get_latest_valid_trading_date():
    tz = pytz.timezone("Asia/Taipei")
    now = datetime.datetime.now(tz)
    today = now.date()

    if now.hour < 15:
        today -= datetime.timedelta(days=1)  # 收盤前回推一天

    while today.weekday() >= 5:  # 週六、週日跳過
        today -= datetime.timedelta(days=1)

    return today.strftime("%Y-%m-%d")

# ========== ✅ 從 Google Sheets 讀取股票代碼 ==========
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

# ========== ✅ 取得熱門前 N 大股票（預設固定列表） ==========
def get_hot_stock_ids(limit=100, filter_type="all"):
    popular_ids = [
        "2330", "2317", "2303", "2603", "3711", "2881", "2454", "2609", "3231",
        "1513", "3707", "8046", "3034", "1101", "1301", "2002", "2882", "2891",
        "2409", "2615", "6147", "8261", "3045", "2344", "4919", "2605", "2408"
    ]
    small_caps = ["8046", "3231", "6147", "3707", "2344", "8261", "4919"]
    large_caps = ["2330", "2317", "2303", "2454", "2881", "2882", "2603", "1101", "1301"]

    base = (popular_ids * ((limit // len(popular_ids)) + 1))[:limit]

    if filter_type == "small_cap":
        base = [sid for sid in base if sid in small_caps]
    elif filter_type == "large_cap":
        base = [sid for sid in base if sid in large_caps]

    # 合併 Google Sheet 額外追蹤股
    sheet_ids = get_google_sheet_stock_ids()
    for sid in sheet_ids:
        if sid not in base:
            base.append(sid)

    return base[:limit]
