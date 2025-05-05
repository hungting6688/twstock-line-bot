import os
from datetime import datetime, timedelta
from modules.finmind_utils import (
    get_latest_valid_trading_date,
    fetch_finmind_data,
    fetch_stock_technical_data,
    get_hot_stock_ids
)


def evaluate_signals(df, score_weights):
    latest = df.iloc[-1]
    score = 0
    reasons = []

    # RSI
    if latest.get("RSI6") is not None:
        if latest["RSI6"] < 30:
            score += score_weights.get("RSI_LOW", 1)
            reasons.append("🟢 RSI < 30 超跌區（RSI）")

    # KD 黃金交叉
    if latest.get("K9") is not None and latest.get("D9") is not None:
        if latest["K9"] > latest["D9"]:
            score += score_weights.get("KD_GOLD", 1)
            reasons.append("🟢 KD 黃金交叉（KD）")

    # 均線交叉
    if latest.get("MA5") and latest.get("MA20"):
        if latest["MA5"] > latest["MA20"]:
            score += score_weights.get("MA_CROSS", 1)
            reasons.append("🟢 MA5 > MA20（均線）")

    # MACD 多頭
    if latest.get("MACD") is not None and latest.get("DIF") is not None:
        if latest["DIF"] > latest["MACD"]:
            score += score_weights.get("MACD_POSITIVE", 1)
            reasons.append("🟢 DIF > MACD（MACD）")

    # 布林通道觸底反彈
    if latest.get("Close") and latest.get("lower_band"):
        if latest["Close"] < latest["lower_band"]:
            score += score_weights.get("BOLLINGER_LOWER", 1)
            reasons.append("🟢 觸及布林下緣（布林）")

    return score, reasons

def analyze_stocks_with_signals(
    mode="closing",
    limit=100,
    min_score=2,
    filter_type="all",
    score_weights=None
):
    print(f"📌 分析模式：{mode}")
    if score_weights is None:
        score_weights = {
            "RSI_LOW": 1,
            "KD_GOLD": 1,
            "MA_CROSS": 1,
            "MACD_POSITIVE": 1,
            "BOLLINGER_LOWER": 1,
        }

    start_date = (datetime.today() - timedelta(days=90)).strftime("%Y-%m-%d")
    end_date = get_latest_valid_trading_date()

    stock_ids = get_hot_stock_ids(limit=limit, filter_type=filter_type)
    print(f"📌 stock_ids 數量：{len(stock_ids)}")
    if not stock_ids:
        return "***收盤綜合推薦總結***\n⚠️ 無熱門股票資料可供分析。"

    results = []
    for stock_id in stock_ids:
        print(f"🔍 正在分析 {stock_id}...")
        try:
            df = fetch_stock_technical_data(stock_id, start_date, end_date)
            if df is None or df.empty:
                print(f"⚠️ {stock_id} 無技術資料")
                continue
            score, reasons = evaluate_signals(df, score_weights)
            if score is None:
                continue
            results.append({
                "stock_id": stock_id,
                "score": score,
                "reasons": reasons
            })
        except Exception as e:
            print(f"❌ 分析 {stock_id} 發生錯誤：{e}")
            continue

    print(f"✅ 成功分析的股票數量：{len(results)}")

    if not results:
        return "***收盤綜合推薦總結***\n⚠️ 今日無法取得任何分析資料。"

    sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
    strong_stocks = [r for r in sorted_results if r["score"] >= min_score]

    msg = "***收盤綜合推薦總結***\n"
    if strong_stocks:
        msg += "\n📈 推薦股票：\n"
        for stock in strong_stocks:
            msg += f"✅ {stock['stock_id']}（分數：{stock['score']}）\n"
            for reason in stock["reasons"]:
                msg += f"　↪ {reason}\n"
    else:
        msg += "\n⚠️ 今日無推薦股票達到門檻。\n"

    # 若無強力推薦，也列出前 2~3 名當作觀察股
    observe_stocks = sorted_results[:3]
    if observe_stocks:
        msg += "\n👀 技術分數前幾名（觀察名單）：\n"
        for stock in observe_stocks:
            msg += f"📌 {stock['stock_id']}（分數：{stock['score']}）\n"
            for reason in stock["reasons"]:
                msg += f"　↪ {reason}\n"

    return msg.strip()
