import argparse
from modules.run_opening import analyze_opening
from modules.intraday_monitor import intraday_check
from modules.dividend import analyze_dividend
from modules.closing_summary import analyze_technical
from modules.line_notify import send_line_notify

def main(mode):
    try:
        if mode == "opening":
            msg = analyze_opening()
        elif mode == "intraday":
            msg = intraday_check()
        elif mode == "dividend":
            # 多股票處理（可手動指定或整合 Google Sheets）
            targets = ["2330", "2603", "2303"]
            msgs = [analyze_dividend(stock_id=s) for s in targets]
            msg = "【午盤法人與股息分析】\n" + "\n\n".join(msgs)
        elif mode == "closing":
            targets = ["2330", "2603", "2303"]
            msgs = [analyze_technical(stock_id=s) for s in targets]
            msg = "【收盤技術總結】\n" + "\n\n".join(msgs)
        else:
            msg = "❌ 無效的模式，請使用 opening / intraday / dividend / closing"
    except Exception as e:
        msg = f"❌ 執行 {mode} 發生錯誤：{e}"

    send_line_notify(msg)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, help="執行模式：opening / intraday / dividend / closing")
    args = parser.parse_args()
    main(args.mode)
