print("[signal_analysis] ✅ 已載入最新版")

from modules.price_fetcher import get_top_stocks
from modules.eps_dividend_scraper import get_eps_data
from modules.ta_analysis import analyze_technical_indicators
from modules.strategy_profiles import get_strategy

def analyze_stocks_with_signals(mode="opening", **kwargs):
    strategy = get_strategy(mode)

    limit = kwargs.get("limit", strategy["limit"])
    min_score = kwargs.get("min_score", strategy["min_score"])
    include_weak = kwargs.get("include_weak", strategy["include_weak"])
    weights = strategy["weights"]

    print(f"[signal] 分析模式：{mode} | 掃描檔數：{limit} | 最低分數：{min_score}")

    try:
        stock_ids = get_top_stocks(limit=limit)
        print(f"[signal] 取得 {len(stock_ids)} 檔股票進行分析")
    except Exception as e:
        print(f"[price_fetcher] ❌ 資料解析失敗：{e}")
        return "[系統錯誤] 無法取得熱門股資訊"

    eps_data = get_eps_data()
    print(f"[EPS] ✅ 成功匯入 EPS 資料筆數：{sum(1 for v in eps_data.values() if v['eps'] is not None)}")
    print(f"[Dividend] ✅ 成功匯入股利資料筆數：{sum(1 for v in eps_data.values() if v['dividend'] is not None)}")

    recommendations = []
    fallback = []

    for sid in stock_ids:
        try:
            result = analyze_technical_indicators(sid, eps_data.get(sid, {}), weights)
            if result:
                score = result.get("score", 0)
                if score >= min_score:
                    recommendations.append((sid, result))
                else:
                    fallback.append((sid, result))
        except Exception as e:
            print(f"[ta_analysis] {sid} 分析失敗：{e}")

    recommendations.sort(key=lambda x: x[1]["score"], reverse=True)
    fallback.sort(key=lambda x: x[1]["score"], reverse=True)

    if not recommendations and fallback:
        print("[signal] 無推薦股，改為推播觀察股")
        recommendations = fallback[:3]

    if not recommendations:
        return f"[{mode.upper()}] 今日無推薦標的"

    msg_lines = [f"[{mode.upper()}] 推薦股票："]
    for sid, result in recommendations:
        score = result["score"]
        signals = "、".join(result.get("signals", []))
        suggestion = result.get("suggestion", "")
        msg_lines.append(f"- {sid}｜分數：{score:.1f}｜訊號：{signals}｜{suggestion}")

    if include_weak:
        weak_list = [sid for sid, r in fallback if r.get("suggestion", "").startswith("不建議")]
        if weak_list:
            msg_lines.append("\n【弱勢提醒】")
            for sid in weak_list[:5]:
                msg_lines.append(f"- {sid}：不建議操作")

    return "\n".join(msg_lines)