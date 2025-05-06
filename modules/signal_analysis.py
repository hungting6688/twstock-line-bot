print("[signal_analysis] ✅ 已載入最新版")

from modules.strategy_profiles import STRATEGY_PROFILES
from modules.price_fetcher import get_top_stocks
from modules.eps_dividend_scraper import get_eps_data
from modules.ta_analysis import analyze_technical_indicators

def analyze_stocks_with_signals(mode="opening", **kwargs):
    profile = STRATEGY_PROFILES.get(mode, {})
    limit = kwargs.get("limit", profile.get("scan_limit", 100))
    min_score = kwargs.get("min_score", profile.get("min_score", 4))
    include_weak = kwargs.get("include_weak", profile.get("include_weak", False))
    indicators = profile.get("indicators", {})
    comment = profile.get("comment", "")

    print(f"[signal] 分析模式：{mode} | 掃描檔數：{limit} | 最低分數：{min_score}")
    
    stock_ids = get_top_stocks(limit=limit)
    print(f"[signal] 取得 {len(stock_ids)} 檔股票進行分析")

    eps_data = get_eps_data()
    results = analyze_technical_indicators(stock_ids, indicators, eps_data)

    recommended = []
    fallback = []

    for sid, info in results.items():
        score = info["score"]
        suggestion = info["suggestion"]
        is_weak = info["is_weak"]

        if score >= min_score:
            recommended.append((sid, score, suggestion))
        elif include_weak and is_weak:
            fallback.append((sid, score, "⚠️ 技術面極弱，請留意風險"))
        else:
            fallback.append((sid, score, suggestion))

    recommended.sort(key=lambda x: -x[1])
    fallback.sort(key=lambda x: -x[1])

    lines = [f"📊【{comment}】"]
    if recommended:
        lines.append("✅ 推薦股票：")
        for sid, score, sugg in recommended:
            lines.append(f"- {sid}（{score}分）：{sugg}")
    else:
        lines.append("⚠️ 無符合推薦門檻，以下為觀察名單：")
        for sid, score, sugg in fallback[:3]:
            lines.append(f"- {sid}（{score}分）：{sugg}")

    return "\n".join(lines)
