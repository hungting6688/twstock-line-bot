# ✅ run_opening.py（支援三類推播：推薦 / 觀察 / 走弱）
from modules.signal_analysis import analyze_stocks_with_signals
from modules.line_bot import send_line_message
from modules.strategy_profiles import get_strategy_profile
from modules.market_sentiment import get_market_sentiment

def analyze_opening():
    print("[run_opening] 開始執行開盤推薦分析...")

    try:
        strategy = get_strategy_profile("opening")
        recommend_min = strategy.get("recommend_min", 6.0)

        result = analyze_stocks_with_signals(mode="opening")
        if not result or result.get("recommended") is None:
            message = "📉 今日無符合條件的推薦股，請持續觀察市場動態。"
            send_line_message(message)
            print("[run_opening] 推播訊息組裝完成 ✅")
            return message

        sentiment_info = get_market_sentiment() if strategy.get("apply_sentiment_adjustment", False) else None
        sentiment_note = f"📊 市場氣氛：{sentiment_info['note']}\n" if sentiment_info else ""

        lines = ["📈 今日開盤推薦結果：", sentiment_note]

        # ✅ 推薦股
        recommended = result.get("recommended", pd.DataFrame())
        if not recommended.empty:
            for _, row in recommended.iterrows():
                lines.append(
                    f"✅ 推薦股｜{row['stock_id']} {row.get('stock_name', '')}｜分數：{row['score']} 分\n"
                    f"➡️ 原因：{row.get('reasons', '-')}\n"
                    f"💡 建議：{row.get('suggestion', '-')}\n"
                )

        # 👀 觀察股
        fallback = result.get("fallback", pd.DataFrame())
        if not fallback.empty:
            lines.append("\n👀 觀察股供參考：")
            for _, row in fallback.iterrows():
                lines.append(
                    f"👀 觀察股｜{row['stock_id']} {row.get('stock_name', '')}｜分數：{row['score']} 分\n"
                    f"➡️ 原因：{row.get('reasons', '-')}\n"
                    f"💡 建議：{row.get('suggestion', '-')}\n"
                )

        # ⚠️ 走弱股
        weak = result.get("weak", pd.DataFrame())
        if not weak.empty:
            lines.append("\n⚠️ 今日走弱股提醒：")
            for _, row in weak.iterrows():
                lines.append(
                    f"⚠️ 走弱股｜{row['stock_id']} {row.get('stock_name', '')}｜分數：{row['score']} 分\n"
                    f"➡️ 原因：{row.get('reasons', '-')}\n"
                    f"💡 建議：{row.get('suggestion', '-')}\n"
                )

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
