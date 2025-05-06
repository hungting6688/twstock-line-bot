import requests
import os

def send_line_message(msg):
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.environ.get("LINE_USER_ID")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "to": user_id,
        "messages": [{
            "type": "text",
            "text": msg
        }]
    }
    url = "https://api.line.me/v2/bot/message/push"
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print("❌ LINE 推播失敗:", response.text)
    else:
        print("✅ LINE 推播成功")
