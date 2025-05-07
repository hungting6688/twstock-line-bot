# modules/closing_summary.py

from modules.signal_analysis import analyze_stocks_with_signals
from modules.line_bot import send_line_message

def analyze_closing():
    print("[closing_summary] ✅ 收盤分析啟動")
    try:
        df_result = analyze_stocks_with_signals(min_turnover=50_000_000, min_score=6, limit=400)

        if df_result.empty:
            message = "📉 收盤觀察：今日無符合中長線條件的推薦股。"
            send_line_message(message)
            return message

        lines = ["📊 收盤總結推薦：\n"]
        for _, row in df_result.iterrows():
            lines.append(
                f"✅ {row['stock_id']} {row['stock_name']}｜分數：{row['score']} 分\n"
                f"➡️ 原因：{row['reasons']}\n"
                f"💡 建議：{row['suggestion']}\n"
            )

        message = "\n".join(lines)
        send_line_message(message)
        print("[closing_summary] 推播完成 ✅")
        return message

    except Exception as e:
        print(f"[closing_summary] ❌ 錯誤：{e}")
        error_msg = "❗ 收盤分析失敗，請稍後再試。"
        send_line_message(error_msg)
        return error_msg
