# main.py

from modules.run_opening import analyze_opening
from modules.line_bot import send_line_bot_message  # ✅ 新增推播功能

def main(mode):
    if mode == "opening":
        msg = analyze_opening()
        print("[main] 分析結果如下：\n", msg)
        send_line_bot_message(message=msg)  # ✅ 實際推播
    else:
        print("不支援的模式")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, required=True)
    args = parser.parse_args()
    main(args.mode)
