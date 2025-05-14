# modules/line_bot.py
print("[line_bot] ✅ 已載入最新版")

import requests
import os

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

def send_line_bot_message(message: str):
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("[line_bot] ❌ 缺少 LINE Token 或 User ID，無法推播")
        return

    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }

    try:
        response = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)
        if response.status_code != 200:
            print(f"[line_bot] ❌ 推播失敗：{response.status_code} - {response.text}")
        else:
            print("[line_bot] ✅ LINE 訊息推播成功")
    except Exception as e:
        print(f"[line_bot] ❌ 推播過程發生錯誤：{e}")
