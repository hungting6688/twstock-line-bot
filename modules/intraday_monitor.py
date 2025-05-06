# modules/intraday_monitor.py

from modules.signal_analysis import analyze_stocks_with_signals
from modules.line_bot import send_line_bot_message

def analyze_intraday():
    print("[intraday_monitor] ✅ 已載入最新版")
    try:
        df_result = analyze_stocks_with_signals(min_turnover=50_000_000, min_score=6)
        if df_result.empty:
            return "📉 中盤時段：目前無明顯強勢股，建議觀望盤勢變化。"

        lines = ["🚀 中盤觀察股推薦：\n"]
        for _, row in df_result.iterrows():
            lines.append(f"📌 {row['stock_id']} {row['stock_name']}｜分數：{row['score']} 分\n➡️ 原因：{row['reasons']}\n💡 建議：{row['suggestion']}\n")

        return "\n".join(lines)

    except Exception as e:
        print(f"[intraday_monitor] ❌ 錯誤：{e}")
        return "❗ 中盤分析失敗，請稍後再試。"
