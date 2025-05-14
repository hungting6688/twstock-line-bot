# modules/run_opening.py
print("[run_opening] ✅ 已載入最新版")

from modules.signal_analysis import analyze_stocks_with_signals
from modules.line_bot import send_line_bot_message
from datetime import datetime

def analyze_opening():
    print("[run_opening] 開始執行開盤推薦分析...")

    try:
        results = analyze_stocks_with_signals(
            strategy_name="opening",
            limit=100,
            min_score=7,
            include_weak=True
        )
    except Exception as e:
        send_line_bot_message(f"[run_opening] ❌ 開盤分析失敗：{str(e)}")
        return

    # 組裝推播訊息
    now = datetime.now().strftime("%Y/%m/%d")
    message = f"📈 {now} 開盤推薦分析結果\n"

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
    print("[run_opening] 推播訊息組裝完成 ✅")
