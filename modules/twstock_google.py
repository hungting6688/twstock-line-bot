import os
import json
import gspread

def get_tracking_stock_ids(sheet_name="追蹤清單", column_index=1) -> list:
    """
    從 Google Sheets 讀取指定欄位（預設 A 欄）中的股票代號清單。
    - 忽略第一列（標題）
    - 只保留純數字代號（如 2330、2603 等）
    - 使用 GitHub Secrets：GOOGLE_JSON_KEY
    """
    google_key_json_str = os.getenv("GOOGLE_JSON_KEY")
    if not google_key_json_str:
        raise ValueError("❌ 未設定 GOOGLE_JSON_KEY 環境變數")
    
    google_key_dict = json.loads(google_key_json_str)
    gc = gspread.service_account_from_dict(google_key_dict)

    sh = gc.open(sheet_name)
    worksheet = sh.sheet1
    col_values = worksheet.col_values(column_index)

    return [v.strip() for v in col_values[1:] if v.strip().isdigit()]
