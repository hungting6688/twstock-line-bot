
import os
from modules.finmind_utils import (
    get_latest_valid_trading_date,
    fetch_stock_technical_data,
    get_hot_stock_ids,
)

def analyze_stocks_with_signals(limit=100, min_score=2.0, filter_type="all", debug=False):
    stock_ids = get_hot_stock_ids(limit=limit, filter_type=filter_type)
    if not stock_ids:
        return (
            "***收盤綜合推薦總結***\n"
            "⚠️ 無熱門股票資料可供分析。\n"
        )

    results = []
    for stock_id in stock_ids:
        date = get_latest_valid_trading_date()
        df = fetch_stock_technical_data(stock_id, start_date="2024-01-01", end_date=date)
        if df is None or df.empty:
            continue

        latest = df.iloc[-1]
        score = 0
        reasons = []

        # 技術分析條件
        if latest["RSI6"] < 30:
            score += 1
            reasons.append("🟢 RSI < 30 超跌區")
        if latest["K9"] > latest["D9"]:
            score += 1
            reasons.append("🟢 KD 黃金交叉")
        if latest["MA5"] > latest["MA20"]:
            score += 1
            reasons.append("🟢 短均穿越長均")
        if latest["DIF"] > latest["MACD"]:
            score += 1
            reasons.append("🟢 MACD 黃金交叉")
        if latest["close"] < latest["lower_band"]:
            score += 1
            reasons.append("🟢 跌破布林下緣")

        results.append({
            "stock_id": stock_id,
            "score": score,
            "reasons": reasons,
        })

    if not results:
        return (
            "***收盤綜合推薦總結***\n"
            "⚠️ 今日無法取得任何分析資料。"
        )

    sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
    recommended = [r for r in sorted_results if r["score"] >= min_score]

    msg = "***收盤綜合推薦總結***\n"

    if recommended:
        for r in recommended:
            reason_str = "；".join(r["reasons"])
            msg += f"\n✅ 推薦：{r['stock_id']}（分數 {r['score']}）\n{reason_str}\n"
    else:
        msg += "⚠️ 今日無符合推薦條件的股票。\n"
        observe = [r for r in sorted_results if r["score"] > 0][:3]
        if observe:
            msg += "\n📌 技術分數前 3 名觀察股：\n"
            for r in observe:
                reason_str = "；".join(r["reasons"])
                msg += f"🔍 {r['stock_id']}（分數 {r['score']}）\n{reason_str}\n"
        else:
            msg += "📭 所有熱門股皆未出現明顯技術反轉訊號。"

    if debug:
        msg += "\n\n🔧 Debug 分數列表：\n"
        for r in sorted_results:
            msg += f"{r['stock_id']}: {r['score']}\n"

    return msg.strip()
