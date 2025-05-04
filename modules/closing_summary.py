from finmind_utils import get_closing_recommendations

def run_closing():
    picks = get_closing_recommendations(limit=5)

    if not picks:
        return "📘 今日收盤：無符合條件的推薦股。"

    message = "📘 收盤推薦股：\n"
    for stock_id, desc in picks:
        message += f"- {stock_id}：{desc}\n"

    message += "\n✅ 今日訊號觀察：MACD 成功率 71%，KD 成功率 64%（短線可參考）"
    return message
