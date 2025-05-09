# ✅ 修正版 run_opening.py（避免 False 錯誤 + 推播穩定）
from modules.signal_analysis import analyze_stocks_with_signals
from modules.line_bot import send_line_message
from modules.strategy_profiles import get_strategy_profile
from modules.market_sentiment import get_market_sentiment

def analyze_opening():
    print("[run_opening] 開始執行開盤推薦分析...")

    try:
        strategy = get_strategy_profile("opening")
        recommend_min = strategy.get("recommend_min", 6.0)

        df_result = analyze_stocks_with_signals(mode="opening")

        if df_result is None or df_result.empty:
            message = "📉 今日無符合條件的推薦股，請持續觀察市場動態。"
            send_line_message(message)
            print("[run_opening] 推播訊息組裝完成 ✅")
            return message

        sentiment_info = get_market_sentiment() if strategy.get("apply_sentiment_adjustment", False) else None
        sentiment_note = f"📊 市場氣氛：{sentiment_info['note']}\n" if sentiment_info else ""

        lines = ["📈 今日開盤推薦結果：", sentiment_note]

        for _, row in df_result.iterrows():
            label = str(row.get("label", "📌"))
            stock_id = str(row.get("stock_id", "-"))
            name = str(row.get("stock_name", ""))
            score = str(row.get("score", "-"))
            reasons = str(row.get("reasons", "-"))
            suggestion = str(row.get("suggestion", "-"))

            lines.append(
                f"{label}｜{stock_id} {name}｜分數：{score} 分\n"
                f"➡️ 原因：{reasons}\n"
                f"💡 建議：{suggestion}\n"
            )

        message = "\n".join(lines)
        send_line_message(message)
        print("[run_opening] 推播訊息組裝完成 ✅")
        return message

    except Exception as e:
        import traceback
        print(f"[run_opening] ❌ 錯誤發生：{repr(e)}")
        traceback.print_exc()
        error_msg = "❗ 開盤分析失敗，請檢查輸出欄位內容。"
        send_line_message(error_msg)
        return error_msg
