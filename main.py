import sys
import os
from dotenv import load_dotenv
from linebot import LineBotApi
from linebot.models import TextSendMessage

# ✅ 若在本地測試需要 .env
load_dotenv()

# ✅ 初始化 LINE Bot API
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
user_id = os.getenv("LINE_USER_ID")

# ✅ 導入各時段模組（你需確保 modules 資料夾中有這些 .py 檔案）
from modules.run_opening import run_opening
from modules.intraday_monitor import run_intraday
from modules.dividend import run_dividend
from modules.closing_summary import run_closing

# ✅ 時段對應邏輯
def run_push(time_code):
    try:
        if time_code == "0900":
            content = run_opening()
        elif time_code == "1030":
            content = run_intraday()
        elif time_code == "1200":
            content = run_dividend()
        elif time_code == "1326":
            content = run_closing()
        else:
            content = f"❌ 無效的時間參數：{time_code}"
        
        # ✅ 發送 LINE 推播
        line_bot_api.push_message(user_id, TextSendMessage(text=content))
        print("✅ 推播成功")
    except Exception as e:
        print("❌ 推播失敗：", str(e))

# ✅ 程式進入點
if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--time":
        run_push(sys.argv[2])
    else:
        print("❗️請使用格式：python3 main.py --time 0900")
