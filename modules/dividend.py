from modules.signal_analysis import analyze_stocks_with_signals
from modules.line_bot import send_line_message
from modules.strategy_profiles import get_strategy_profile

def analyze_dividend():
    print("[dividend] ✅ 開始執行配息分析...")

    try:
        strategy = get_strategy_profile("dividend")
        min_score = strategy["min_score"]
        df_result = analyze_stocks_with_signals(mode="dividend")

        if df_result is None or df_result.empty:
            message = "📉 配息分析無推薦或觀察股"
            send_line_message(message)
            return message

        lines = ["💰 配息機會股推薦：\n"]
        for _, row in df_result.iterrows():
            label = "✅ 推薦股" if row["score"] >= min_score else "👀 觀察股"
            lines.append(
                f"{label}｜{row['stock_id']} {row['stock_name']}｜分數：{row['score']} 分\n"
                f"➡️ 原因：{row['reasons']}\n"
                f"💡 建議：{row['suggestion']}\n"
            )

        message = "\n".join(lines)
        send_line_message(message)
        return message

    except Exception as e:
        print(f"[dividend] ❌ 錯誤：{e}")
        error_msg = "❗ 配息分析失敗"
        send_line_message(error_msg)
        return error_msg
