from modules.run_opening import analyze_opening
from modules.intraday_monitor import analyze_intraday  # ✅ 加這行
from modules.dividend import analyze_dividend
from modules.closing_summary import analyze_closing

def main(mode: str):
    print(f"[main] 分析模式：{mode}")
    if mode == "opening":
        msg = analyze_opening()
    elif mode == "intraday":
        msg = analyze_intraday()  # ✅ 加這行
    elif mode == "dividend":
        msg = analyze_dividend()
    elif mode == "closing":
        msg = analyze_closing()
    else:
        print("不支援的模式.並且無推播通知")
        return
    
    from modules.line_bot import send_line_bot_message
    send_line_bot_message(msg)
    print("[LINE BOT] ✅ 推播成功")
