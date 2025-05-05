import argparse
from modules.run_opening import analyze_opening
from modules.intraday_monitor import analyze_intraday
from modules.dividend import analyze_dividend
from modules.closing_summary import analyze_closing
from modules.line_bot_push import send_line_bot_message

def main(mode):
    if mode == "opening":
        msg = analyze_opening()
    elif mode == "intraday":
        msg = analyze_intraday()
    elif mode == "dividend":
        msg = analyze_dividend()
    elif mode == "closing":
        msg = analyze_closing()
    else:
        msg = "❌ 無效的 mode 參數，請使用：opening / intraday / dividend / closing"
    
    send_line_bot_message(msg)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, help="執行模式：opening / intraday / dividend / closing")
    args = parser.parse_args()
    main(args.mode)
