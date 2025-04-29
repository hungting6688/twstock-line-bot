# twstock_sheet_utils.py

import os
import json
import base64
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def load_google_sheets():
    # 從 GitHub Secrets / .env 環境變數中讀取金鑰
    key_json_base64 = os.getenv("GOOGLE_SHEET_KEY_JSON")
    sheet_id = os.getenv("GOOGLE_SHEET_ID")

    if not key_json_base64 or not sheet_id:
        raise Exception("缺少 GOOGLE_SHEET_KEY_JSON 或 GOOGLE_SHEET_ID 設定")

    key_json_str = base64.b64decode(key_json_base64).decode('utf-8')
    key_json = json.loads(key_json_str)

    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(key_json, scope)
    client = gspread.authorize(credentials)

    sheet = client.open_by_key(sheet_id)
    worksheet = sheet.get_worksheet(0)  # 讀取第一個工作表
    return worksheet

def get_watchlist():
    worksheet = load_google_sheets()
    data = worksheet.col_values(1)  # 讀取 A 欄（第 1 欄）
    stock_ids = [d.strip() for d in data if d.strip().isdigit()]
    return stock_ids

if __name__ == "__main__":
    # 測試用
    watchlist = get_watchlist()
    print("目前追蹤股票代碼：", watchlist)
