import os
from dotenv import load_dotenv
from linebot import LineBotApi
from linebot.models import TextSendMessage

# 載入 .env（如果你是本地測試）
load_dotenv()

# 取得金鑰與使用者 ID
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
user_id = os.getenv("LINE_USER_ID")

# 傳送測試訊息
line_bot_api.push_message(user_id, TextSendMessage(text="📢 測試推播成功！來自 GitHub Actions 🚀"))

print("✅ 測試訊息已送出")
