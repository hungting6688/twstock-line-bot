import gspread
from google.oauth2.service_account import Credentials
import json

def load_sheet_data():
    with open("twstock-bot-c384c7951791.json") as f:
        keyfile_dict = json.load(f)

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(keyfile_dict, scopes=scopes)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(os.getenv("GOOGLE_SHEET_ID")).sheet1
    rows = sheet.get_all_records()
    return rows

