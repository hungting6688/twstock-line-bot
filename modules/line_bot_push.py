import os
import requests

def send_line_bot_message(message: str, user_id: str = None):
    access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    if not access_token:
        raise ValueError("❌ 尚未設定 LINE_CHANNEL_ACCESS_TOKEN")

    user_id = user_id or os.getenv("LINE_USER_ID")
    if not user_id:
        raise ValueError("❌ 尚未設定 LINE_USER_ID（接收者 LINE ID）")

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}]
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code != 200:
            print(f"❌ LINE Bot 推播失敗：{res.status_code} {res.text}")
        else:
            print("✅ LINE Bot 推播成功")
    except Exception as e:
        print(f"❌ 傳送訊息時發生錯誤：{e}")
