print("[signal_analysis] ✅ 已載入最新版")

from modules.ta_analysis import analyze_technical_indicators
from modules.price_fetcher import get_realtime_top_stocks
from modules.eps_dividend_scraper import get_eps_data
from modules.strategy_profiles import STRATEGY_PROFILES

def analyze_stocks_with_signals(mode="opening", **kwargs):
    profile = STRATEGY_PROFILES.get(mode, {})
    scan_limit = kwargs.get("scan_limit", profile.get("scan_limit"))
    min_score = kwargs.get("min_score", profile.get("min_score"))
    include_weak = kwargs.get("include_weak", profile.get("include_weak", False))
    weights = profile.get("weights", {})
    indicators = profile.get("indicators", [])

    print(f"[signal] 分析模式：{mode} | 掃描檔數：{scan_limit} | 最低分數：{min_score}")

    stock_list = get_realtime_top_stocks(limit=scan_limit)
    print(f"[signal] 取得 {len(stock_list)} 檔股票進行分析")

    eps_data = get_eps_data()
    print(f"[EPS] ✅ 成功匯入 EPS 資料筆數：{len(eps_data)}")
    print(f"[Dividend] ✅ 成功匯入股利資料筆數：{sum(1 for d in eps_data.values() if d['dividend'] is not None)}")

    results = []
    for stock_id in stock_list:
        try:
            indicators_result = analyze_technical_indicators(stock_id)
            score = 0.0
            reasons = []

            for ind in indicators:
                if ind in indicators_result and indicators_result[ind]["signal"]:
                    weight = weights.get(ind, 1.0)
                    score += weight
                    reasons.append(indicators_result[ind]["reason"])

            # EPS / Dividend 加分
            if "eps" in weights and stock_id in eps_data and eps_data[stock_id]["eps"]:
                score += weights["eps"]
                reasons.append("EPS 穩定成長")
            if "dividend" in weights and stock_id in eps_data and eps_data[stock_id]["dividend"]:
                score += weights["dividend"]
                reasons.append("穩定配息")

            results.append({
                "stock_id": stock_id,
                "score": round(score, 2),
                "reasons": reasons
            })

        except Exception as e:
            print(f"[ta_analysis] {stock_id} 分析失敗：{e}")
            continue

    # 推薦與觀察股篩選
    recommendations = [r for r in results if r["score"] >= min_score]
    fallback = sorted(results, key=lambda x: x["score"], reverse=True)[:3]

    msg = f"[{mode.upper()} 推薦結果]\n"
    if recommendations:
        for r in sorted(recommendations, key=lambda x: x["score"], reverse=True):
            msg += f"✅ {r['stock_id']} | 分數 {r['score']} 分\n－" + "；".join(r["reasons"]) + "\n"
    else:
        msg += "⚠️ 無推薦股，以下為觀察名單：\n"
        for r in fallback:
            msg += f"🔍 {r['stock_id']} | 分數 {r['score']} 分\n－" + "；".join(r["reasons"]) + "\n"

    return msg
