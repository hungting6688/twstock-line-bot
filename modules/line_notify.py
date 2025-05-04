import os
import requests

def send_line_notify(message: str, token_env: str = "LINE_USER_ID"):
    token = os.getenv(token_env)

    if not token:
        print(f"⚠️ 未找到環境變數 {token_env}，略過推播")
        return

    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"message": message}

    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 200:
            print(f"❌ LINE 推播失敗：{response.text}")
        else:
            print("✅ LINE 推播成功")
    except Exception as e:
        print(f"❌ 發送 LINE 訊息時出錯：{e}")