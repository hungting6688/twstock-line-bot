print("[signal_analysis] ✅ 已載入最新版")

from modules.price_fetcher import fetch_top_stocks
from modules.ta_analysis import analyze_technical_indicators
from modules.eps_dividend_scraper import get_eps_data
from modules.strategy_profiles import STRATEGY_PROFILES

def analyze_stocks_with_signals(mode: str) -> str:
    config = STRATEGY_PROFILES.get(mode, {})
    limit = config.get("scan_limit", 100)
    min_score = config.get("min_score", 3.5)
    include_weak = config.get("include_weak", False)
    indicators = config.get("indicators", [])

    print(f"[signal] 分析模式：{mode} | 掃描檔數：{limit} | 最低分數：{min_score}")

    stock_list = fetch_top_stocks(limit=limit)
    print(f"[signal] 取得 {len(stock_list)} 檔股票進行分析")

    eps_data = get_eps_data()
    result_lines = []
    fallback_lines = []

    for stock_id, stock_df in stock_list.items():
        score = 0
        reasons = []
        suggestions = []

        signals = analyze_technical_indicators(stock_df)
        if not signals:
            continue

        for ind in indicators:
            if ind in ["macd", "kd", "ma"] and signals.get(ind):
                score += 1
                reasons.append(ind.upper())
            if ind == "rsi":
                rsi_val = signals.get("rsi", 50)
                if rsi_val < 30:
                    score += 1
                    reasons.append("RSI < 30")
                elif rsi_val > 70 and include_weak:
                    reasons.append("RSI > 70")

        # EPS 與 Dividend 條件
        eps = eps_data.get(stock_id, {}).get("eps")
        dividend = eps_data.get(stock_id, {}).get("dividend")
        if "eps" in indicators and eps is not None and eps > 1.5:
            score += 1
            reasons.append("EPS > 1.5")
        if "dividend" in indicators and dividend is not None and dividend > 2.0:
            score += 1
            reasons.append("高股利")

        # 建議文字
        suggestions.extend(signals.get("suggestions", []))
        if eps and eps > 3:
            suggestions.append("EPS 穩健成長，基本面良好")
        if dividend and dividend > 3:
            suggestions.append("配息大於 3 元，適合存股")

        message = f"📈 {stock_id} | 分數：{score}\n"
        message += "📊 條件：" + "、".join(reasons) + "\n"
        if suggestions:
            message += "💡 建議：" + "；".join(suggestions) + "\n"

        if score >= min_score:
            result_lines.append(message)
        elif include_weak:
            fallback_lines.append(message)

    if result_lines:
        return "\n".join(result_lines[:5])
    elif fallback_lines:
        return "⚠️ 今日無強烈推薦股，以下為觀察股：\n" + "\n".join(fallback_lines[:3])
    else:
        return "⚠️ 今日無符合條件之推薦股"
