# modules/line_bot.py

import os
import requests

def send_line_bot_message(message: str):
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.environ.get("LINE_USER_ID")

    if not token or not user_id:
        print("[LINE BOT] ❌ 缺少 LINE_CHANNEL_ACCESS_TOKEN 或 LINE_USER_ID")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {
        "to": user_id,
        "messages": [{"type": "text", "text": message[:1000]}]  # LINE 單則訊息上限 1000 字
    }

    url = "https://api.line.me/v2/bot/message/push"
    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        print(f"[LINE BOT] ❌ 推播失敗：{response.status_code}, {response.text}")
    else:
        print("[LINE BOT] ✅ 推播成功")
