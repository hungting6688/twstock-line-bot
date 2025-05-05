import argparse
from modules.line_bot_push import send_line_bot_message
from modules.run_opening import analyze_run_opening
from modules.intraday_monitor import analyze_intraday_monitor
from modules.dividend import analyze_dividend
from modules.closing_summary import analyze_closing_summary

def main(mode: str):
    print(f"📌 分析模式：{mode}")
    
    if mode == "opening":
        msg = analyze_run_opening()
    elif mode == "intraday":
        msg = analyze_intraday_monitor()
    elif mode == "dividend":
        msg = analyze_dividend()
    elif mode == "closing":
        msg = analyze_closing_summary()
    else:
        msg = "❌ 錯誤：未知的分析模式，請使用 opening / intraday / dividend / closing 其中之一。"
    
    send_line_bot_message(msg)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, required=True, help="選擇分析模式")
    args = parser.parse_args()
    main(args.mode)
