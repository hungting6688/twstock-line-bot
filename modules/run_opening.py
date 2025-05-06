from modules.signal_analysis import analyze_stocks_with_signals

def format_message(df):
    if df.empty:
        return "📉 今日無符合條件的推薦股，請持續觀察市場動態。"

    lines = ["📈 今日開盤推薦股：\n"]
    for _, row in df.iterrows():
        line = f"✅ {row['stock_id']} {row['stock_name']}｜分數：{row['score']} 分\n➡️ 原因：{row['reasons']}\n💡 建議：{row['suggestion']}\n"
        lines.append(line)
    return "\n".join(lines)

def analyze_opening():
    print("[run_opening] 開始執行開盤推薦分析...")

    try:
        df_result = analyze_stocks_with_signals(min_turnover=50000000, min_score=5)
        message = format_message(df_result)
        print("[run_opening] 推播訊息組裝完成 ✅")
        return message

    except Exception as e:
        print(f"[run_opening] 錯誤發生：{e}")
        return "❗ 開盤分析失敗，請檢查伺服器或資料來源。"
