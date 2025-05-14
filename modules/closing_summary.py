print("[closing_summary] ✅ 已載入最新版")

from modules.signal_analysis import analyze_stocks_with_signals
from modules.line_bot import send_line_bot_message
from datetime import datetime

def analyze_closing():
    print("[closing_summary] ⏳ 執行收盤分析...")

    try:
        results = analyze_stocks_with_signals(
            strategy_name="closing",
            limit=300,
            min_score=6,
            include_weak=True,
            filter_type=None
        )
    except Exception as e:
        send_line_bot_message(f"[closing_summary] ❌ 收盤分析失敗：{str(e)}")
        return

    now = datetime.now().strftime("%Y/%m/%d")
    message = f"📉 {now} 15:00 收盤總結分析\n"

    if results["recommended"]:
        message += "\n✅ 推薦股：\n"
        for stock in results["recommended"]:
            message += f"🔹 {stock['stock_id']} {stock['name']}｜分數：{stock['score']}\n➡️ {stock['reason']}\n💡 建議：{stock['suggestion']}\n\n"
    else:
        message += "\n✅ 推薦股：無\n"

    if results["watchlist"]:
        message += "\n📌 觀察股（分數高但未達門檻）：\n"
        for stock in results["watchlist"]:
            message += f"🔸 {stock['stock_id']} {stock['name']}｜分數：{stock['score']}\n➡️ {stock['reason']}\n\n"

    if results["weak"]:
        message += "\n⚠️ 走弱警示股：\n"
        for stock in results["weak"]:
            message += f"❗ {stock['stock_id']} {stock['name']}｜走弱原因：{stock['reason']}\n"

    send_line_bot_message(message.strip())
    print("[closing_summary] 推播完成 ✅")
