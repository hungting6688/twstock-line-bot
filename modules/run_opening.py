# modules/run_opening.py

from modules.signal_analysis import analyze_stocks_with_signals
from modules.line_bot import send_line_message

def analyze_opening():
    print("[run_opening] 開始執行開盤推薦分析...")

    try:
        # 擷取與分析熱門股（成交金額門檻與分數門檻可調）
        df_result = analyze_stocks_with_signals(min_turnover=50_000_000, min_score=5)

        # 無推薦結果時
        if df_result.empty:
            message = "📉 今日無符合條件的推薦股，請持續觀察市場動態。"
            send_line_message(message)
            return message

        # 有推薦結果，格式化訊息
        lines = ["📈 今日開盤推薦股：\n"]
        for _, row in df_result.iterrows():
            lines.append(
                f"✅ {row['stock_id']} {row['stock_name']}｜分數：{row['score']} 分\n"
                f"➡️ 原因：{row['reasons']}\n"
                f"💡 建議：{row['suggestion']}\n"
            )

        message = "\n".join(lines)
        send_line_message(message)
        print("[run_opening] 推播訊息組裝完成 ✅")
        return message

    except Exception as e:
        print(f"[run_opening] ❌ 錯誤發生：{e}")
        error_msg = "❗ 開盤分析失敗，請檢查伺服器或資料來源。"
        send_line_message(error_msg)
        return error_msg

# ✅ 如需單獨測試此模組時可執行
if __name__ == "__main__":
    analyze_opening()
