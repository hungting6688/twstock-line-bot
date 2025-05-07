# modules/intraday_monitor.py

from modules.signal_analysis import analyze_stocks_with_signals
from modules.line_bot import send_line_message

def analyze_intraday():
    print("[intraday_monitor] ✅ 中盤分析啟動")
    try:
        df_result = analyze_stocks_with_signals(min_turnover=50_000_000, min_score=6, limit=100)
        
        if df_result.empty:
            message = "📉 中盤時段：目前無明顯強勢股，建議觀望盤勢變化。"
            send_line_message(message)
            return message

        lines = ["🚀 中盤觀察股推薦：\n"]
        for _, row in df_result.iterrows():
            lines.append(
                f"📌 {row['stock_id']} {row['stock_name']}｜分數：{row['score']} 分\n"
                f"➡️ 原因：{row['reasons']}\n"
                f"💡 建議：{row['suggestion']}\n"
            )

        message = "\n".join(lines)
        send_line_message(message)
        print("[intraday_monitor] 推播完成 ✅")
        return message

    except Exception as e:
        print(f"[intraday_monitor] ❌ 錯誤：{e}")
        error_msg = "❗ 中盤分析失敗，請稍後再試。"
        send_line_message(error_msg)
        return error_msg
