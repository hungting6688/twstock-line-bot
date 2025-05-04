from data_utils import get_top_100_stocks
from indicator_utils import is_rsi_strong, is_macd_upward, is_kd_positive

def run_opening():
    candidate_stocks = get_top_100_stocks()
    selected = []

    for stock_id in candidate_stocks:
        signals = 0
        if is_rsi_strong(stock_id):
            signals += 1
        if is_macd_upward(stock_id):
            signals += 1
        if is_kd_positive(stock_id):
            signals += 1
        if signals >= 2:
            selected.append(stock_id)

    if not selected:
        return "📈 早盤觀察：今日熱門股中無明顯強勢續漲個股。"

    message = "📈 早盤觀察推薦：\n"
    for stock in selected[:5]:  # 最多推播五檔
        message += f"- {stock}：動能轉強、資金流入、短線表現可期\n"

    return message
