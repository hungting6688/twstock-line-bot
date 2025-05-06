# modules/line_bot.py

import os
import requests

def send_line_bot_message(msg: str):
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.environ.get("LINE_USER_ID")

    if not token or not user_id:
        print("[line_bot] ❌ 找不到 LINE Token 或 User ID")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    body = {
        "to": user_id,
        "messages": [{
            "type": "text",
            "text": msg
        }]
    }

    response = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers=headers,
        json=body
    )

    if response.status_code == 200:
        print("[line_bot] ✅ 訊息發送成功")
    else:
        print(f"[line_bot] ❌ 發送失敗：{response.text}")
