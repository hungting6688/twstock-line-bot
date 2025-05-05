# modules/line_bot_push.py

import os
import requests

def send_line_bot_message(message):
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.environ.get("LINE_USER_ID")

    if not token:
        raise ValueError("❌ 尚未設定 LINE_CHANNEL_ACCESS_TOKEN")
    if not user_id:
        raise ValueError("❌ 尚未設定 LINE_USER_ID")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    payload = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}]
    }

    url = "https://api.line.me/v2/bot/message/push"
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        print("⚠️ LINE 推播失敗", response.text)
    else:
        print("✅ LINE Bot 推播成功")
