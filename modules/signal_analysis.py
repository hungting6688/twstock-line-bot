# modules/signal_analysis.py
print("[signal_analysis] ✅ 已載入最新版")

from modules.price_fetcher import get_top_stocks
from modules.ta_analysis import analyze_technical_indicators
from modules.eps_dividend_scraper import get_eps_data, get_dividend_data

def analyze_stocks_with_signals(
    mode="opening",
    limit=100,
    min_score=4,
    filter_type=None,
    include_weak=True
):
    if mode == "opening":
        title = "📌 分析模式：opening"
    elif mode == "intraday":
        title = "📌 分析模式：intraday"
    elif mode == "dividend":
        title = "📌 分析模式：dividend"
    elif mode == "closing":
        title = "📌 分析模式：closing"
    else:
        title = f"📌 分析模式：{mode}"

    print(f"[signal] 開始分析前 {limit} 檔熱門股...")

    stock_ids = get_top_stocks(limit=limit, filter_type=filter_type)
    print(f"[signal] 取得 {len(stock_ids)} 檔股票進行分析")

    tech_results = analyze_technical_indicators(stock_ids)
    print(f"[signal] 技術分析完成 {len(tech_results)} 檔")

    eps_data = get_eps_data()
    dividend_data = get_dividend_data()

    recommend = []
    fallback = []
    weak_list = []

    for sid in tech_results:
        score = tech_results[sid]["score"]
        suggestion = tech_results[sid]["suggestion"]
        is_weak = tech_results[sid]["is_weak"]

        if score >= min_score:
            recommend.append(f"{sid} | Score: {score} | {suggestion}")
        else:
            fallback.append((score, f"{sid} | Score: {score} | {suggestion}"))

        if include_weak and is_weak:
            weak_list.append(sid)

    message = f"{title}\n"

    if recommend:
        message += "✅ 推薦股票：\n" + "\n".join(recommend[:5]) + "\n"
    else:
        fallback_sorted = sorted(fallback, key=lambda x: -x[0])
        top_fallbacks = [item[1] for item in fallback_sorted[:3]]
        message += "（無股票達推薦標準，列出觀察股）\n" + "\n".join(top_fallbacks) + "\n"

    if include_weak and weak_list:
        message += "\n⚠️ 極弱提醒：\n"
        for sid in weak_list[:3]:
            message += f"{sid} | RSI 過低 + 跌破均線，短線轉弱請留意風險。\n"

    return message.strip()
