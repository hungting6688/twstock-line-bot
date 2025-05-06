# modules/signal_analysis.py

from modules.price_fetcher import get_top_stocks
from modules.ta_analysis import analyze_technical_indicators
from modules.eps_dividend_scraper import get_eps_data

def analyze_stocks_with_signals(
    mode: str,
    limit: int = 100,
    min_score: int = 3,
    include_weak: bool = False,
    filter_type: str = None,
    stock_ids: list[str] = None
):
    if stock_ids is None:
        stock_ids = get_top_stocks(limit=limit, filter_type=filter_type)

    price_data = analyze_technical_indicators(stock_ids)
    eps_data = get_eps_data()

    result_lines = []
    recommended = []
    observed = []
    weak_alerts = []

    for sid in stock_ids:
        pdata = price_data.get(sid)
        if not pdata:
            continue

        score = pdata.get("score", 0)
        comment = pdata.get("suggestion", "")
        weak = pdata.get("is_weak", False)
        eps_info = eps_data.get(sid, {})

        eps_txt = ""
        if eps_info:
            eps_val = eps_info.get("eps")
            div_val = eps_info.get("dividend")
            if eps_val is not None:
                eps_txt += f" | EPS: {eps_val}"
            if div_val is not None:
                eps_txt += f" / 配息: {div_val}"

        line = f"{sid} | Score: {score} | {comment}{eps_txt}"

        if score >= min_score:
            recommended.append((score, line))
        else:
            observed.append((score, line))

        if include_weak and weak:
            weak_alerts.append(f"⚠️ {sid} 為極弱股，請留意觀察。")

    recommended.sort(reverse=True)
    observed.sort(reverse=True)

    result_lines.append(f"📌 分析模式：{mode}")

    if recommended:
        result_lines.append("✅ 推薦股票：")
        result_lines.extend([line for _, line in recommended])
    else:
        result_lines.append("（無股票達推薦標準，列出觀察股）")
        result_lines.extend([line for _, line in observed[:3]])

    if include_weak and weak_alerts:
        result_lines.append("\n❗極弱股提示：")
        result_lines.extend(weak_alerts)

    return "\n".join(result_lines)
