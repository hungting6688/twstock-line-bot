from finmind_utils import get_top_dividend_stocks

def run_dividend():
    top_dividends = get_top_dividend_stocks(limit=5)

    if not top_dividends:
        return "💰 今日無公告或預估殖利率較高的個股。"

    message = "💰 高殖利率觀察：\n"
    for stock_id, percent in top_dividends:
        message += f"- {stock_id}：預估殖利率 {percent}%\n"
    return message
