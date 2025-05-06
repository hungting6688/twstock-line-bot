# modules/signal_analysis.py

print("[signal_analysis] ✅ 已載入最新版")

from modules.ta_analysis import analyze_technical_indicators
from modules.price_fetcher import get_top_stocks
from modules.eps_dividend_scraper import get_eps_data
from modules.strategy_profiles import STRATEGY_PROFILES

def analyze_stocks_with_signals(mode="opening"):
    strategy = STRATEGY_PROFILES.get(mode, STRATEGY_PROFILES["opening"])
    limit = strategy["scan_limit"]
    min_score = strategy["min_score"]
    include_weak = strategy.get("include_weak", False)
    indicators = strategy["indicators"]
    comment = strategy["comment"]

    print(f"[signal] 分析模式：{mode} | 掃描檔數：{limit} | 最低分數：{min_score}")
    stock_ids = get_top_stocks(limit=limit)
    print(f"[signal] 取得 {len(stock_ids)} 檔股票進行分析")

    eps_data = get_eps_data()
    tech_results = analyze_technical_indicators(stock_ids, indicators=indicators, eps_data=eps_data)

    recommend = []
    weak_alerts = []

    for sid, res in tech_results.items():
        if res["score"] >= min_score:
            recommend.append((sid, res))
        elif include_weak and res.get("is_weak"):
            weak_alerts.append((sid, res))

    recommend.sort(key=lambda x: x[1]["score"], reverse=True)

    # 推播文字
    msg = f"📌 分析模式：{mode}\n"
    if recommend:
        msg += "✅ 推薦股票：\n"
        for sid, res in recommend:
            msg += f"{sid} | Score: {res['score']} | {res['suggestion']}\n"
    else:
        msg += "（無股票達推薦標準，列出觀察股）\n"
        top_candidates = sorted(tech_results.items(), key=lambda x: x[1]["score"], reverse=True)[:5]
        for sid, res in top_candidates:
            msg += f"{sid} | Score: {res['score']} | {res['suggestion']}\n"

    if weak_alerts:
        msg += "\n⚠️ 極弱提醒：\n"
        for sid, res in weak_alerts:
            msg += f"{sid} | {res['suggestion']}\n"

    return msg.strip()
