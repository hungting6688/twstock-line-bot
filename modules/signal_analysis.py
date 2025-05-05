from modules.ta_analysis import analyze_signals
from modules.price_fetcher import fetch_price_data
from modules.stock_data_utils import get_all_stock_ids
from datetime import datetime

def analyze_stocks_with_signals(date: str, limit: int = 100, min_score: float = 2.0, filter_type: str = "all", include_weak: bool = False) -> str:
    stock_ids = get_all_stock_ids(limit=limit, filter_type=filter_type)
    results = []

    for stock_id in stock_ids:
        try:
            df = fetch_price_data(stock_id)
            if df is None or df.empty:
                continue
            info = analyze_signals(df.iloc[-1])
            results.append({
                "stock_id": stock_id,
                "score": info["score"],
                "reasons": info["reasons"],
                "suggestions": info["suggestions"]
            })
        except Exception as e:
            continue

    if not results:
        return f"***title***\n⚠️ 今日無法取得任何分析資料。"

    sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
    good = [r for r in sorted_results if r["score"] >= min_score]
    weak = [r for r in sorted_results if r["score"] <= -2.5] if include_weak else []

    msg = "***title***\n"

    if good:
        msg += "\n📈 推薦股：\n"
        for item in good:
            msg += f"🔹 {item['stock_id']}（分數 {item['score']}）\n"
            msg += f"   {'；'.join(item['reasons'])}\n"

    else:
        fallback = sorted_results[:3]
        msg += "\n📌 無符合推薦門檻的股票，供觀察：\n"
        for item in fallback:
            msg += f"🔸 {item['stock_id']}（分數 {item['score']}）\n"
            msg += f"   {'；'.join(item['reasons'])}\n"

    if weak:
        msg += "\n⚠️ 極弱股提醒：\n"
        for item in weak[:3]:
            msg += f"🔻 {item['stock_id']}（分數 {item['score']}）\n"
            msg += f"   {'；'.join(item['reasons'])}\n"

    return msg.strip()
