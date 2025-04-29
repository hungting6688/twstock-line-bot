import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

def load_sheet_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    keyfile_dict = json.loads(os.getenv("GOOGLE_SHEET_KEY_JSON"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(keyfile_dict, scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(os.getenv("GOOGLE_SHEET_ID")).sheet1
    rows = sheet.get_all_values()
    stock_list = []

    for row in rows[1:]:  # 跳過標題列
        if not row or not row[0].strip():
            continue
        stock = {
            "代碼": row[0].strip(),
            "備註": row[1].strip() if len(row) > 1 else "",
            "目標價": row[2].strip() if len(row) > 2 else "",
            "提醒條件": row[3].strip() if len(row) > 3 else "",
        }
        stock_list.append(stock)

    return stock_list

