# run_opening.py
from signal_analysis import analyze_stocks_with_signals
from line_bot import send_line_bot_message

def format_message(df):
    if df.empty:
        return "📉 今日無符合條件的推薦股，請持續觀察市場動態。"

    lines = ["📈 今日開盤推薦股：\n"]
    for _, row in df.iterrows():
        line = f"✅ {row['stock_id']} {row['stock_name']}｜分數：{row['score']} 分\n➡️ 原因：{row['reasons']}\n💡 建議：{row['suggestion']}\n"
        lines.append(line)
    return "\n".join(lines)

def main():
    print("[run_opening] 開始執行開盤推薦分析...")
    
    try:
        df_result = analyze_stocks_with_signals(min_turnover=50000000, min_score=5)
        message = format_message(df_result)
        send_line_bot_message(message)
        print("[run_opening] 推播完成 ✅")
    
    except Exception as e:
        print(f"[run_opening] 錯誤發生：{e}")
        send_line_bot_message("❗ 開盤分析失敗，請檢查伺服器或資料來源。")

if __name__ == "__main__":
    main()
