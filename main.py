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
            # 可自訂多檔股票分析
            stock_ids = ["2330", "2603", "2303"]
            msgs = [analyze_dividend(stock_id=sid) for sid in stock_ids]
            msg = "【午盤法人與股息分析】\n" + "\n\n".join(msgs)

        elif mode == "closing":
            stock_ids = ["2330", "2603", "2303"]
            msgs = [analyze_technical(stock_id=sid) for sid in stock_ids]
            msg = "【收盤技術總結】\n" + "\n\n".join(msgs)

        else:
            msg = f"❌ 無效的模式：{mode}，請使用 opening / intraday / dividend / closing"

        # ✅ 空訊息處理
        if not msg or msg.strip() == "":
            msg = f"✅ {mode} 模式執行完成，但今日無資料或無推薦結果"

    except Exception as e:
        msg = f"❌ 執行 {mode} 發生錯誤：{e}"

    # ✅ LINE 推播
    send_line_notify(msg)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, help="執行模式：opening / intraday / dividend / closing")
    args = parser.parse_args()
    main(args.mode)
