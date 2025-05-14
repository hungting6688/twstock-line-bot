print("[dividend] ✅ 已載入最新版")

from modules.signal_analysis import analyze_stocks_with_signals
from modules.line_bot import send_line_bot_message
from datetime import datetime

def analyze_dividend():
    print("[dividend] ⏳ 執行配息分析...")

    try:
        results = analyze_stocks_with_signals(
            strategy_name="dividend",
            limit=100,
            min_score=6.5,
            include_weak=True,
            filter_type="small_cap"
        )
    except Exception as e:
        send_line_bot_message(f"[dividend] ❌ 配息分析失敗：{str(e)}")
        return

    now = datetime.now().strftime("%Y/%m/%d")
    message = f"💰 {now} 12:00 配息潛力股報告\n"

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
    print("[dividend] 推播完成 ✅")
