# ✅ run_opening.py（加上 row 印出以偵測 False 錯誤來源）
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

        for idx, row in df_result.iterrows():
            try:
                print(f"[debug] row[{idx}] = {row.to_dict()}")  # ✅ 印出整列原始資料

                label = str(row.get("label") or "📌")
                stock_id = str(row.get("stock_id") or "")
                stock_name = str(row.get("stock_name") or "")
                score = str(row.get("score") or "-")
                reasons = str(row.get("reasons") or "-")
                suggestion = str(row.get("suggestion") or "-")

                lines.append(
                    f"{label}｜{stock_id} {stock_name}｜分數：{score} 分\n"
                    f"➡️ 原因：{reasons}\n"
                    f"💡 建議：{suggestion}\n"
                )
            except Exception as row_err:
                print(f"[run_opening] ⚠️ 單列錯誤：{repr(row_err)} at row {idx}")

        message = "\n".join(lines)
        send_line_message(message)
        print("[run_opening] 推播訊息組裝完成 ✅")
        return message

    except Exception as e:
        import traceback
        print(f"[run_opening] ❌ 錯誤發生：{repr(e)}")
        traceback.print_exc()
        send_line_message("❗ 開盤推播失敗，請檢查資料格式或欄位內容。")
        return "[run_opening] ❌ 推播失敗"
