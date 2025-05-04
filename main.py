
import argparse
from modules.run_opening import analyze_opening
from modules.intraday_monitor import analyze_intraday
from modules.dividend import analyze_dividend
from modules.closing_summary import analyze_closing
from modules.line_bot_push import send_line_bot_message

def main(mode, limit):
    if mode == "opening":
        msg = analyze_opening(limit=limit)
    elif mode == "intraday":
        msg = analyze_intraday(limit=limit)
    elif mode == "dividend":
        msg = analyze_dividend(limit=limit)
    elif mode == "closing":
        msg = analyze_closing(limit=limit)
    else:
        raise ValueError("❌ mode 參數錯誤，請使用 opening / intraday / dividend / closing")
    send_line_bot_message(msg)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, required=True, help="執行模式：opening / intraday / dividend / closing")
    parser.add_argument("--limit", type=int, default=100, help="熱門股分析數量，預設為 100")
    args = parser.parse_args()
    main(args.mode, args.limit)

