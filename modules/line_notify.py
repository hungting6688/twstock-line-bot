import os
import requests

def send_line_notify(message: str):
    token = os.getenv("LINE_NOTIFY_TOKEN")
    if not token:
        raise ValueError("❌ 未設定 LINE_NOTIFY_TOKEN 環境變數")
    
    url = "https://notify-api.line.me/api/notify"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {"message": message}
    response = requests.post(url, headers=headers, data=data)

    if response.status_code != 200:
        print("❌ LINE 推播失敗")
    else:
        print("✅ LINE 推播成功")
