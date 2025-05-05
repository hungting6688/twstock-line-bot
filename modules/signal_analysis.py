import pandas as pd
from modules.ta_analysis import analyze_signals
from modules.price_fetcher import fetch_price_data
from modules.stock_data_utils import get_latest_valid_trading_date, get_all_stock_ids

def analyze_stocks_with_signals(
    title: str,
    min_score: float = 2.0,
    limit: int = 100,
    filter_type: str = "all",  # 可選 "all", "large_cap", "small_cap"
    include_weak: bool = False
) -> str:
    msg = f"{title}\n"
    date = get_latest_valid_trading_date()

    # 取得股票代碼（含 ETF，過濾下市）
    stock_ids = get_all_stock_ids(limit=limit, filter_type=filter_type)

    results = []
    for stock_id in stock_ids:
        df = fetch_price_data(stock_id, date)
        if df is None or len(df) < 30:
            continue
        analysis = analyze_signals(df)
        results.append({
            "stock_id": stock_id,
            "score": analysis["score"],
            "reasons": analysis["reasons"],
            "warnings": analysis["warnings"]
        })

    if not results:
        msg += "⚠️ 今日無法取得任何分析資料。"
        return msg

    # 排序，推薦股與觀察股
    sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
    recommended = [r for r in sorted_results if r["score"] >= min_score]
    observed = sorted_results[:3] if not recommended else []

    if recommended:
        msg += "\n📈 推薦股票（符合條件）\n"
        for r in recommended:
            msg += format_stock_result(r)

    if observed:
        msg += "\n📊 技術觀察（分數最高但未達推薦門檻）\n"
        for r in observed:
            msg += format_stock_result(r)

    if include_weak:
        weak_list = [r for r in sorted_results if r["score"] <= 0 and any("⚠️" in w for w in r["warnings"])]
        if weak_list:
            msg += "\n🔻 極弱警示股（技術面偏空）\n"
            for r in weak_list[:3]:
                msg += format_stock_result(r)

    return msg.strip()


def format_stock_result(r):
    reasons = "\n".join(r["reasons"]) if r["reasons"] else "（無明確利多訊號）"
    warnings = "\n".join(r["warnings"]) if r["warnings"] else ""
    block = f"\n➡️ {r['stock_id']}（總分 {r['score']}）\n{reasons}"
    if warnings:
        block += f"\n{warnings}"
    return block + "\n"
