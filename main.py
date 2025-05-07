# main.py

print("[main] ✅ 主程式已載入")

import argparse
from modules.line_bot import send_line_message

# 延遲載入，避免未使用時提前執行
analyzers = {
    "opening": lambda: __import__("modules.run_opening", fromlist=["analyze_opening"]).analyze_opening(),
    "intraday": lambda: __import__("modules.intraday_monitor", fromlist=["analyze_intraday"]).analyze_intraday(),
    "dividend": lambda: __import__("modules.dividend", fromlist=["analyze_dividend"]).analyze_dividend(),
    "closing": lambda: __import__("modules.closing_summary", fromlist=["analyze_closing"]).analyze_closing()
}

def main(mode: str):
    print(f"[main] 分析模式：{mode}")

    if mode in analyzers:
        msg = analyzers[mode]()
    else:
        print("❌ 不支援的模式，請使用 --mode=[opening|intraday|dividend|closing]")
        return

    if msg:
        print("[main] ⚠️ 分析模組已自行推播，無需重複發送")
    else:
        print("[main] ⚠️ 無推播內容")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, required=True, help="分析模式 [opening|intraday|dividend|closing]")
    args = parser.parse_args()
    main(args.mode)
