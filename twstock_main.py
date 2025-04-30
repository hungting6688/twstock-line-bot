import sys
import os
sys.path.append(os.path.dirname(__file__))

import requests
from dotenv import load_dotenv
from datetime import datetime
from twstock_sheet_utils import load_sheet_data
from twstock_recommend import get_recommend_stocks
from tech_rank import get_tech_recommend
from twstock_macd import analyze_macd_signal

load_dotenv()

# ✅ 加入這行診斷 Secret 是否存在
print("📢 GOOGLE_SHEET_KEY_JSON =", os.getenv("GOOGLE_SHEET_KEY_JSON"))

LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")

def get_fake_rsi_dict():
    return {
        "8046": 73,
        "2603": 72,
        "2884": 74
    }

def get_macd_recommend_list():
    rsi_dict = get_fake_rsi_dict()
    hot_stocks = ["8046", "2603", "2884"]
    macd_results = []
    for code in hot_stocks:
        result = analyze_macd_signal(code, rsi_dict)
        if result:
            macd_results.append(result)
    return macd_results

def analyze_stock_triggers(now: datetime):
    slot_labels = {
        9: "📊 開盤推播（09:00）",
        10: "🚀 早盤追蹤（10:00）",
        12: "📈 中午觀察（12:00）",
        13: "📌 午後提醒（13:15）"
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

    lines.append("\n📈 MACD 技術推薦：")
    macd_results = get_macd_recommend_list()
    if macd_results:
        for result in macd_results:
            lines.append(f"推薦 {result['code']} → {result['reason']}")
    else:
        lines.append("（目前無符合 MACD 條件的股票）")

    lines.append("\n📉 中小型股推薦：")
    for rec in get_recommend_stocks():
        lines.append(f"推薦 {rec['code']}（{rec['name']}）→ {rec['reason']}")

    lines.append(f"\n（分析時間：{now.strftime('%H:%M')}）")
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
