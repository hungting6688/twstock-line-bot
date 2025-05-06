print("[signal_analysis] ✅ 已載入最新版")

from modules.price_fetcher import get_top_stocks
from modules.eps_dividend_scraper import get_eps_data
from modules.ta_analysis import analyze_technical_indicators
from modules.strategy_profiles import STRATEGY_PROFILES

def analyze_stocks_with_signals(mode: str = "opening", **kwargs) -> str:
    print(f"[signal] 分析模式：{mode} | 取得策略設定中...")

    profile = STRATEGY_PROFILES.get(mode, {})
    scan_limit = kwargs.get("scan_limit", profile.get("scan_limit"))
    min_score = kwargs.get("min_score", profile.get("min_score"))
    include_weak = kwargs.get("include_weak", profile.get("include_weak"))
    indicators = profile.get("indicators", {})
    comment = profile.get("comment", "")

    print(f"[signal] 分析模式：{mode} | 掃描檔數：{scan_limit} | 最低分數：{min_score}")
    stock_list = get_top_stocks(limit=scan_limit)
    print(f"[signal] 取得 {len(stock_list)} 檔股票進行分析")

    eps_data = get_eps_data()
    results = analyze_technical_indicators(stock_list, indicators=indicators, eps_data=eps_data)

    recommend = []
    fallback = []

    for sid, info in results.items():
        if info["score"] >= min_score:
            recommend.append((sid, info))
        else:
            fallback.append((sid, info))

    recommend.sort(key=lambda x: x[1]["score"], reverse=True)
    fallback.sort(key=lambda x: x[1]["score"], reverse=True)

    messages = [f"[{mode.upper()}] {comment}\n"]
    if recommend:
        messages.append("✅ 今日推薦：")
        for sid, info in recommend[:5]:
            messages.append(f"{sid}｜分數：{info['score']}｜{info['suggestion']}")
    else:
        messages.append("⚠️ 無推薦股，以下為觀察股：")
        for sid, info in fallback[:3]:
            messages.append(f"{sid}｜分數：{info['score']}｜{info['suggestion']}")

    if include_weak:
        weak_list = [(sid, info) for sid, info in results.items() if info["is_weak"]]
        weak_list.sort(key=lambda x: x[1]["score"])
        if weak_list:
            messages.append("\n📉 技術面偏弱提醒：")
            for sid, info in weak_list[:5]:
                messages.append(f"{sid}｜分數：{info['score']}｜{info['suggestion']}")

    return "\n".join(messages)
