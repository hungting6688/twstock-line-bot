# modules/line_bot.py

import os
import requests

print("[line_bot] ✅ 已載入最新版")

def send_line_message(message: str):
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.getenv("LINE_USER_ID")

    if not token or not user_id:
        print("[line_bot] ❌ 找不到 LINE Token 或 User ID，請確認 Secrets 設定")
        return

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    body = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}]
    }

    try:
        res = requests.post(url, headers=headers, json=body)
        if res.status_code == 200:
            print("[line_bot] ✅ 訊息成功發送")
        else:
            print(f"[line_bot] ❌ 發送失敗，錯誤碼：{res.status_code}")
            print(res.text)
    except Exception as e:
        print(f"[line_bot] ❌ 發送過程出現錯誤：{e}")
