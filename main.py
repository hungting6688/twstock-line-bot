# main.py

print("[main] ✅ 主程式已載入")

import argparse
from modules.run_opening import analyze_opening
from modules.intraday_monitor import analyze_intraday
from modules.dividend import analyze_dividend
from modules.closing_summary import analyze_closing
from modules.line_bot import send_line_message

def main(mode: str):
    print(f"[main] 分析模式：{mode}")
    if mode == "opening":
        msg = analyze_opening()
    elif mode == "intraday":
        msg = analyze_intraday()
    elif mode == "dividend":
        msg = analyze_dividend()
    elif mode == "closing":
        msg = analyze_closing()
    else:
        print("❌ 不支援的模式，請使用 --mode=[opening|intraday|dividend|closing]")
        return

    send_line_message(msg)
    print("[LINE BOT] ✅ 推播成功")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, required=True, help="分析模式 [opening|intraday|dividend|closing]")
    args = parser.parse_args()
    main(args.mode)
