from modules.signal_analysis import analyze_stocks_with_signals
from modules.line_bot import send_line_message

def analyze_intraday():
    print("[intraday_monitor] ✅ 開始執行中盤分析...")

    try:
        df_result = analyze_stocks_with_signals(
            min_turnover=30_000_000,
            min_score=4,
            limit=120,
            fallback_top_n=5
        )

        if df_result.empty:
            message = "📉 中盤分析無推薦或觀察股"
            send_line_message(message)
            return message

        lines = ["⏱️ 中盤潛力股推薦：\n"]
        for _, row in df_result.iterrows():
            label = "🌟 推薦股" if row["score"] >= 4 else "👀 觀察股"
            lines.append(
                f"{label}｜{row['stock_id']} {row['stock_name']}｜分數：{row['score']} 分\n"
                f"➡️ 原因：{row['reasons']}\n"
                f"💡 建議：{row['suggestion']}\n"
            )

        message = "\n".join(lines)
        send_line_message(message)
        return message

    except Exception as e:
        print(f"[intraday_monitor] ❌ 錯誤：{e}")
        error_msg = "❗ 中盤分析失敗"
        send_line_message(error_msg)
        return error_msg
