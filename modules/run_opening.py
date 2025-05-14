print("[run_opening] ✅ 已載入最新版")

from modules.signal_analysis import analyze_stocks_with_signals
from modules.line_bot import send_line_bot_message
from datetime import datetime

def analyze_opening():
    print("[run_opening] 開始執行開盤推薦分析...")

    try:
        results = analyze_stocks_with_signals(
            mode="opening",  # ✅ 修正 key 名稱為 mode（與 signal_analysis 相符）
            limit=100,
            min_score=7,
            include_weak=True
        )
    except Exception as e:
        send_line_bot_message(f"[run_opening] ❌ 開盤分析失敗：{str(e)}")
        return

    # 整理分群
    recommended = [r for r in results if r["label"] == "✅ 推薦"]
    watchlist = [r for r in results if r["label"] == "📌 觀察"]
    weaklist = [r for r in results if r["label"] == "⚠️ 走弱"]

    # 組裝推播訊息
    now = datetime.now().strftime("%Y/%m/%d")
    message = f"📈 {now} 開盤推薦分析結果\n"

    if recommended:
        message += "\n✅ 推薦股：\n"
        for stock in recommended:
            message += f"🔹 {stock['stock_id']} {stock['name']}｜分數：{stock['score']}\n"
    else:
        message += "\n✅ 推薦股：無\n"

    if watchlist:
        message += "\n📌 觀察股：\n"
        for stock in watchlist:
            message += f"🔸 {stock['stock_id']} {stock['name']}｜分數：{stock['score']}\n"

    if weaklist:
        message += "\n⚠️ 走弱股：\n"
        for stock in weaklist:
            message += f"❗ {stock['stock_id']} {stock['name']}｜分數：{stock['score']}\n"

    send_line_bot_message(message.strip())
    print("[run_opening] 推播訊息組裝完成 ✅")
