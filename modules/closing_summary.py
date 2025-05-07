from modules.signal_analysis import analyze_stocks_with_signals
from modules.line_bot import send_line_message

def analyze_closing():
    print("[closing_summary] ✅ 開始執行收盤分析...")

    try:
        df_result = analyze_stocks_with_signals(
            min_turnover=40_000_000,
            min_score=4.8,
            limit=300,
            fallback_top_n=7
        )

        if df_result.empty:
            message = "📉 收盤無推薦或觀察股"
            send_line_message(message)
            return message

        lines = ["🔔 收盤推薦分析：\n"]
        for _, row in df_result.iterrows():
            label = "🌟 推薦股" if row["score"] >= 4.8 else "👀 觀察股"
            lines.append(
                f"{label}｜{row['stock_id']} {row['stock_name']}｜分數：{row['score']} 分\n"
                f"➡️ 原因：{row['reasons']}\n"
                f"💡 建議：{row['suggestion']}\n"
            )

        message = "\n".join(lines)
        send_line_message(message)
        return message

    except Exception as e:
        print(f"[closing_summary] ❌ 錯誤：{e}")
        error_msg = "❗ 收盤分析失敗"
        send_line_message(error_msg)
        return error_msg
