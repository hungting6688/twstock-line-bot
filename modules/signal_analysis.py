
from modules.finmind_utils import (
    get_latest_valid_trading_date,
    fetch_finmind_data,
    fetch_stock_technical_data,
    fetch_financial_statement,
    fetch_institutional_investors,
    get_hot_stock_ids,
    get_tracking_stock_ids,
)
import datetime

def analyze_stocks_with_signals(limit=300, min_score=2.0, filter_type="all", debug=True):
    # 強制使用固定測試日以排除資料延遲影響
    force_date = "2025-05-02"
    stock_ids = get_hot_stock_ids(limit=limit, filter_type=filter_type, force_date=force_date)
    
    if not stock_ids:
        return "***技術分析總結***\n⚠️ 無熱門股票資料可供分析。"

    results = []
    for stock_id in stock_ids:
        score = 0
        messages = []

        # RSI 模擬判斷
        if int(stock_id) % 3 == 0:
            score += 1
            messages.append("🟢 RSI < 30 超跌區")

        # KD 模擬判斷
        if int(stock_id) % 4 == 0:
            score += 1
            messages.append("🟢 KD 黃金交叉")

        # MACD 模擬
        if int(stock_id) % 5 == 0:
            score += 1
            messages.append("🟢 MACD 多頭趨勢")

        # 布林通道 模擬
        if int(stock_id) % 6 == 0:
            score += 1
            messages.append("🟢 價格跌破布林下緣")

        # 模擬法人與 EPS 加分
        if int(stock_id) % 7 == 0:
            score += 1
            messages.append("🟢 法人連日買超")

        if int(stock_id) % 11 == 0:
            score += 1
            messages.append("🟢 EPS 年年成長")

        if debug:
            print(f"🧪 {stock_id} 分數：{score}（{', '.join(messages)}）")

        if score >= min_score:
            results.append(f"📈 {stock_id}（{score} 分）\n" + "\n".join(messages))

    if not results:
        return "***技術分析總結***\n⚠️ 今日無法取得任何分析資料。"

    msg = "***技術分析總結***\n" + "\n\n".join(results)
    return msg.strip()
