# modules/closing_summary.py

from modules.signal_analysis import analyze_stocks_with_signals
from modules.line_bot import send_line_bot_message

def analyze_closing():
    print("[closing_summary] ✅ 已載入最新版")
    try:
        df_result = analyze_stocks_with_signals(min_turnover=50_000_000, min_score=6)
        if df_result.empty:
            return "📉 收盤觀察：今日無符合中長線條件的推薦股。"

        lines = ["📊 收盤總結推薦：\n"]
        for _, row in df_result.iterrows():
            lines.append(f"✅ {row['stock_id']} {row['stock_name']}｜分數：{row['score']} 分\n➡️ 原因：{row['reasons']}\n💡 建議：{row['suggestion']}\n")

        return "\n".join(lines)

    except Exception as e:
        print(f"[closing_summary] ❌ 錯誤：{e}")
        return "❗ 收盤分析失敗，請稍後再試。"
