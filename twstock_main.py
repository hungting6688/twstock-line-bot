import sys
from datetime import datetime
from modules.run_opening import run as run_opening
from modules.intraday_monitor import run as run_intraday
from modules.dividend import run as run_dividend
from modules.closing_summary import run as run_closing

def push_0900():
    print("📊 [0900] 執行早盤開盤前技術分析")
    run_opening()

def push_1030():
    print("📊 [1030] 執行盤中追蹤與異常偵測")
    run_intraday()

def push_1200():
    print("📊 [1200] 執行午盤股息/推薦股分析")
    run_dividend()

def push_1326():
    print("📊 [1326] 執行收盤總結與統計")
    run_closing()

def run_push(time_code):
    print(f"🚀 啟動每日股市分析推播 | 時段：{time_code} | 時間：{datetime.now()}")
    if time_code == "0900":
        push_0900()
    elif time_code == "1030":
        push_1030()
    elif time_code == "1200":
        push_1200()
    elif time_code == "1326":
        push_1326()
    else:
        print("⚠️ 無效的時間參數，請使用 0900 / 1030 / 1200 / 1326")

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--time":
        run_push(sys.argv[2])
    else:
        print("❗ 請使用格式：python3 main.py --time 0900")
