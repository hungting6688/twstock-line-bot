import datetime
from modules.ta_analysis import analyze_signals
from modules.eps_dividend_scraper import get_eps_data, get_dividend_yield
from modules.stock_data_utils import get_stock_name

def analyze_stocks_with_signals(
    stock_ids,
    title="📌 股票分析",
    min_score=2.0,
    include_weak=False
):
    today = datetime.date.today()
    eps_data = get_eps_data()
    dividend_data = get_dividend_yield()

    results = []
    weak_stocks = {}

    for stock_id in stock_ids:
        stock_name = get_stock_name(stock_id)
        signals, score, weak_reasons = analyze_signals(stock_id)

        if not signals and not weak_reasons:
            continue

        # 技術分數不足，記錄為觀察或極弱
        if score < min_score:
            if include_weak and weak_reasons:
                weak_stocks[f"{stock_id} {stock_name}"] = weak_reasons
            results.append({
                "stock_id": stock_id,
                "stock_name": stock_name,
                "score": score,
                "signals": signals
            })
            continue

        results.append({
            "stock_id": stock_id,
            "stock_name": stock_name,
            "score": score,
            "signals": signals
        })

    if not results and not weak_stocks:
        return f"{title}\n⚠️ 今日無法取得任何分析資料。"

    # 推薦與觀察股排序
    recommended = [r for r in results if r["score"] >= min_score]
    observed = [r for r in results if r["score"] < min_score]
    recommended.sort(key=lambda x: x["score"], reverse=True)
    observed.sort(key=lambda x: x["score"], reverse=True)

    # 組合推播訊息
    msg = f"{title}\n📅 {today.strftime('%Y-%m-%d')}\n"
    if recommended:
        msg += "\n✅ 推薦觀察股：\n"
        for r in recommended:
            signal_str = "、".join(r["signals"])
            msg += f"🔹 {r['stock_id']} {r['stock_name']}（分數：{r['score']}）\n👉 {signal_str}\n"

    if not recommended and observed:
        msg += "\n☁️ 今日無推薦股，以下為技術分數前幾名：\n"
        for r in observed[:3]:
            signal_str = "、".join(r["signals"])
            msg += f"🔸 {r['stock_id']} {r['stock_name']}（分數：{r['score']}）\n👉 {signal_str}\n"

    if include_weak and weak_stocks:
        msg += "\n⚠️ 極弱觀察股（建議避開）:\n"
        for sid, reasons in weak_stocks.items():
            msg += f"🔻 {sid}：{'、'.join(reasons)}\n"

    return msg.strip()
