
import os
import pandas as pd
from modules.finmind_utils import (
    get_latest_valid_trading_date,
    fetch_stock_technical_data,
    fetch_financial_statement,
    fetch_institutional_investors,
    get_hot_stock_ids,
    get_tracking_stock_ids
)

def analyze_stocks_with_signals(limit=100, min_score=2.0, filter_type="all", debug=False):
    stock_ids = get_hot_stock_ids(limit=limit, filter_type=filter_type)
    sheet_ids = get_tracking_stock_ids()
    stock_ids = list(set(stock_ids + sheet_ids))

    if not stock_ids:
        return (
            "***技術分析總結***\n"
            "⚠️ 無熱門股票資料可供分析。"
        )

    date = get_latest_valid_trading_date()
    results = []

    for stock_id in stock_ids:
        df = fetch_stock_technical_data(stock_id, start_date="2024-01-01", end_date=date)
        if df is None or df.empty:
            continue
        latest = df.iloc[-1]

        score = 0
        reasons = []

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

        # 法人 5 日買超加分
        inst_df = fetch_institutional_investors(stock_id)
        if inst_df is not None and not inst_df.empty:
            recent = inst_df[inst_df["date"] <= date].tail(5)
            if recent["net_buy"].sum() > 0:
                score += 1
                reasons.append("🟢 法人 5 日買超")

        # EPS 成長加分
        eps_df = fetch_financial_statement(stock_id)
        if eps_df is not None and not eps_df.empty:
            eps_df = eps_df.sort_values("date")
            if len(eps_df) >= 2:
                latest_eps = eps_df.iloc[-1]["EPS"]
                prev_eps = eps_df.iloc[-2]["EPS"]
                if latest_eps > prev_eps:
                    score += 1
                    reasons.append("🟢 EPS 年增率為正")

        results.append({
            "stock_id": stock_id,
            "score": score,
            "reasons": reasons
        })

    if not results:
        return "***技術分析總結***\n⚠️ 今日無法取得任何分析資料。"

    sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
    recommended = [r for r in sorted_results if r["score"] >= min_score]
    observed = [r for r in sorted_results if r["score"] < min_score and r["score"] > 0][:3]
    weak = [r for r in sorted_results if r["score"] <= 0][:3]

    msg = "***技術分析總結***\n"

    if recommended:
        msg += "\n✅ 推薦股：\n"
        for r in recommended:
            reasons = "；".join(r["reasons"])
            msg += f"{r['stock_id']}（分數 {r['score']}）：{reasons}\n"
    else:
        msg += "\n⚠️ 今日無符合推薦條件的股票。"

    if observed:
        msg += "\n\n📌 技術分數前 3 名觀察股：\n"
        for r in observed:
            reasons = "；".join(r["reasons"])
            msg += f"🔍 {r['stock_id']}（分數 {r['score']}）：{reasons}\n"

    if weak:
        msg += "\n\n⚠️ 技術面極弱前 3 名（風險提醒）：\n"
        for r in weak:
            msg += f"🔻 {r['stock_id']}（分數 {r['score']}）\n"

    if debug:
        msg += "\n\n🔧 Debug 分數：\n"
        for r in sorted_results:
            msg += f"{r['stock_id']}：{r['score']}\n"

    return msg.strip()
