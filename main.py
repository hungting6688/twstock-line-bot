import argparse
from modules.run_opening import analyze_opening
from modules.intraday_monitor import intraday_check
from modules.dividend import analyze_dividend
from modules.closing_summary import analyze_technical
from modules.line_notify import send_line_notify


def main(mode):
    if mode == "opening":
        msg = analyze_opening()
    elif mode == "intraday":
        msg = intraday_check()
    elif mode == "dividend":
        msg = analyze_dividend()
    elif mode == "closing":
        msg = analyze_technical()
    else:
        msg = "❌ 無效的模式，請使用 opening / intraday / dividend / closing"
    send_line_notify(msg)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, help="執行模式：opening / intraday / dividend / closing")
    args = parser.parse_args()
    main(args.mode)
