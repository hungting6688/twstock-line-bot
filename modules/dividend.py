# modules/dividend.py

from modules.signal_analysis import analyze_stocks_with_signals
from modules.line_bot import send_line_bot_message

def analyze_dividend():
    print("[dividend] ✅ 已載入最新版")
    try:
        df_result = analyze_stocks_with_signals(min_turnover=30_000_000, min_score=5)
        if df_result.empty:
            return "📉 午盤觀察：無短線機會股推薦，建議持續觀察。"

        lines = ["💹 午盤短線潛力股推薦：\n"]
        for _, row in df_result.iterrows():
            lines.append(f"⭐ {row['stock_id']} {row['stock_name']}｜分數：{row['score']} 分\n➡️ 原因：{row['reasons']}\n💡 建議：{row['suggestion']}\n")

        return "\n".join(lines)

    except Exception as e:
        print(f"[dividend] ❌ 錯誤：{e}")
        return "❗ 午盤分析失敗，請稍後再試。"
