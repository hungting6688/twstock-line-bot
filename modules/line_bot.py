# modules/line_bot.py
import requests
import os

print("[line_bot] ✅ 已載入最新版")

def send_line_message(msg: str):
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.environ.get("LINE_USER_ID")

    if not token or not user_id:
        print("[line_bot] ❌ 缺少 LINE TOKEN 或 USER ID，無法推播")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "to": user_id,
        "messages": [{
            "type": "text",
            "text": msg
        }]
    }

    try:
        response = requests.post(
            "https://api.line.me/v2/bot/message/push",
            headers=headers,
            json=payload
        )
        if response.status_code == 200:
            print("[LINE BOT] ✅ 推播成功")
        else:
            print(f"[LINE BOT] ❌ 推播失敗：{response.status_code} - {response.text}")
    except Exception as e:
        print(f"[LINE BOT] ❌ 發送異常：{e}")
