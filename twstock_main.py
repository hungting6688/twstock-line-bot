# twstock_main.py

import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# 載入 GitHub Secrets（或本地 .env）
load_dotenv()

LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")

def get_dummy_analysis(now: datetime) -> str:
    # 模擬推播內容（之後可換成技術分析模組）
    hour = now.hour
    time_slot = {
        8: "📈 撮合預測推播（08:30）",
        9: "🚀 開盤強弱速報（09:00）",
        12: "📊 中午技術異常整理（12:00）",
        13: "⚠️ 盤中轉折觀察（13:00）",
        14: "📘 收盤完整分析（13:40）"
    }
    label = time_slot.get(hour, "🧠 測試推播（非預定時段）")
    return f"{label}\n\n✅ 今日技術面轉強：2330、2454\n🔮 預估殖利率前 3 名：長榮、華航、國巨"

def send_line_notify(message: str):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    response = requests.post(url, headers=headers, json=body)
    print("LINE 推播結果:", response.status_code, response.text)

if __name__ == "__main__":
    now = datetime.now()
    content = get_dummy_analysis(now)
    send_line_notify(content)
