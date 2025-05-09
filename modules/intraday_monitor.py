from modules.signal_analysis import analyze_stocks_with_signals
from modules.line_bot import send_line_message

def analyze_intraday():
    print("[intraday_monitor] 開始執行盤中監控分析...")

    try:
        df_result = analyze_stocks_with_signals(
            min_turnover=50_000_000,
            min_score=4.5,
            eps_limit=150,
            stock_limit=150,
            mode="intraday"
        )

        if df_result is None or df_result.empty:
            message = "📉 盤中無符合條件的推薦股。"
            send_line_message(message)
            return message

        lines = ["📊 盤中推薦結果：\n"]
        for _, row in df_result.iterrows():
            label = "✅ 推薦股" if row["score"] >= 4.5 else "👀 觀察股"
            lines.append(
                f"{label}｜{row['stock_id']} {row['stock_name']}｜分數：{row['score']} 分\n"
                f"➡️ 原因：{row['reasons']}\n"
                f"💡 建議：{row['suggestion']}\n"
            )

        message = "\n".join(lines)
        send_line_message(message)
        print("[intraday_monitor] 推播訊息組裝完成 ✅")
        return message

    except Exception as e:
        print(f"[intraday_monitor] ❌ 錯誤發生：{e}")
        error_msg = "❗ 盤中分析失敗，請檢查伺服器或資料來源。"
        send_line_message(error_msg)
        return error_msg
