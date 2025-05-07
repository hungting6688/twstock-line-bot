from modules.signal_analysis import analyze_stocks_with_signals
from modules.line_bot import send_line_message

def analyze_opening():
    print("[run_opening] 開始執行開盤推薦分析...")

    try:
        df_result = analyze_stocks_with_signals(
            min_turnover=50_000_000,
            min_score=5,
            limit=100,
            fallback_top_n=5
        )

        if df_result.empty:
            message = "📉 今日無推薦或觀察股，請持續關注市場。"
            send_line_message(message)
            return message

        lines = ["📈 今日開盤推薦結果：\n"]
        for _, row in df_result.iterrows():
            label = "🌟 推薦股" if row["score"] >= 5 else "👀 觀察股"
            lines.append(
                f"{label}｜{row['stock_id']} {row['stock_name']}｜分數：{row['score']} 分\n"
                f"➡️ 原因：{row['reasons']}\n"
                f"💡 建議：{row['suggestion']}\n"
            )

        message = "\n".join(lines)
        send_line_message(message)
        print("[run_opening] 推播訊息組裝完成 ✅")
        return message

    except Exception as e:
        print(f"[run_opening] ❌ 錯誤發生：{e}")
        error_msg = "❗ 開盤分析失敗，請檢查伺服器或資料來源。"
        send_line_message(error_msg)
        return error_msg
