from finmind_utils import get_intraday_breakout_stocks

def run_intraday():
    breakout_list = get_intraday_breakout_stocks(limit=5)

    if not breakout_list:
        return "📊 即時監控：目前未偵測到異常放量或技術轉強的個股。"

    message = "📊 即時技術觀察推薦：\n"
    for stock_id, reason in breakout_list:
        message += f"- {stock_id}：{reason}\n"
    return message
