import sys
import os
sys.path.append(os.path.dirname(__file__))

import requests
from dotenv import load_dotenv
from datetime import datetime
from twstock_sheet_utils import load_sheet_data
from twstock_recommend import get_recommend_stocks

load_dotenv()

LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")

def analyze_stock_triggers(now: datetime):
    slot_labels = {
        8: "📊 撮合預測推播（08:30）",
        9: "🚀 開盤強弱速報（09:00）",
        12: "📈 中午技術異常整理（12:00）",
        13: "📌 盤中轉折觀察（13:00）",
        14: "📘 收盤完整分析（13:40）"
    }
    label = slot_labels.get(now.hour, "🧪 測試推播")
    lines = [f"{label}\n"]

    stock_list = load_sheet_data()
    for stock in stock_list:
        code = stock["代碼"]
        note = stock["備註"]
        condition = stock["提醒條件"]
        reason = ""

        if "每日提醒" in condition:
            reason = "每日提醒"
        elif "RSI" in condition or "均線" in condition or "MACD" in condition:
            reason = condition

        if reason:
            lines.append(f"推薦 {code}（{note or '無備註'}）→ {reason}")

    # 中小型股推薦整合段落
    lines.append("\n📈 中小型股推薦：")
    for rec in get_recommend_stocks():
        lines.append(f"推薦 {rec['code']}（{rec['name']}）→ {rec['reason']}")

    return "\n".join(lines)

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
    summary = analyze_stock_triggers(now)
    send_line_notify(summary)
