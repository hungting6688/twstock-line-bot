import os
import requests

def send_line_bot_message(message: str, user_id: str = None):
    access_token = os.getenv("LINE_CHANNEL_TOKEN")
    if not access_token:
        raise ValueError("❌ 尚未設定 LINE_CHANNEL_TOKEN")

    # 預設對象（可寫死或從 Secrets 提供）
    user_id = user_id or os.getenv("LINE_USER_ID")
    if not user_id:
        raise ValueError("❌ 尚未設定 LINE_USER_ID（接收訊息的用戶 ID）")

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}]
    }

    res = requests.post(url, headers=headers, json=payload)
    if res.status_code != 200:
        print(f"❌ 推播失敗：{res.status_code} {res.text}")
    else:
        print("✅ LINE Bot 推播成功")