# modules/dividend.py

from modules.signal_analysis import analyze_stocks_with_signals
from modules.line_bot import send_line_message

def analyze_dividend():
    print("[dividend] ✅ 午盤分析啟動")
    try:
        df_result = analyze_stocks_with_signals(min_turnover=30_000_000, min_score=5, limit=150)

        if df_result.empty:
            message = "📉 午盤觀察：無短線機會股推薦，建議持續觀察。"
            send_line_message(message)
            return message

        lines = ["💹 午盤短線潛力股推薦：\n"]
        for _, row in df_result.iterrows():
            lines.append(
                f"⭐ {row['stock_id']} {row['stock_name']}｜分數：{row['score']} 分\n"
                f"➡️ 原因：{row['reasons']}\n"
                f"💡 建議：{row['suggestion']}\n"
            )

        message = "\n".join(lines)
        send_line_message(message)
        print("[dividend] 推播完成 ✅")
        return message

    except Exception as e:
        print(f"[dividend] ❌ 錯誤：{e}")
        error_msg = "❗ 午盤分析失敗，請稍後再試。"
        send_line_message(error_msg)
        return error_msg
