
import os
import json
from datetime import datetime
import requests
from dotenv import load_dotenv
from twstock_sheet_utils import load_sheet_data

load_dotenv()

LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")

def send_line_notify(message: str):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    res = requests.post(url, headers=headers, json=payload)
    print("LINE 推播結果:", res.status_code, res.text)

if __name__ == "__main__":
    now = datetime.now()
    rows = load_sheet_data()
    summary = f"📊 推播測試：讀取 {len(rows)} 筆資料成功！\n分析時間：{now.strftime('%H:%M')}"
    send_line_notify(summary)
