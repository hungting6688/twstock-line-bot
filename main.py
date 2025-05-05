import argparse
from modules.run_opening import analyze_opening
from modules.intraday_monitor import analyze_intraday
from modules.dividend import analyze_dividend
from modules.closing_summary import analyze_closing
from modules.line_bot import send_line_message

def main(mode: str):
    print(f"📌 分析模式：{mode}")

    if mode == "opening":
        msg = analyze_opening()
    elif mode == "monitor":
        msg = analyze_intraday()
    elif mode == "dividend":
        msg = analyze_dividend()
    elif mode == "closing":
        msg = analyze_closing()
    else:
        print("❌ 錯誤：請指定模式為 opening / monitor / dividend / closing")
        return

    print(msg)
    send_line_message(msg)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, help="執行模式：opening / monitor / dividend / closing")
    args = parser.parse_args()
    main(args.mode)
