print("[signal_analysis] ✅ 已載入最新版")

from modules.price_fetcher import get_top_stocks
from modules.eps_dividend_scraper import get_eps_and_dividend
from modules.ta_analysis import analyze_technical_indicators
from modules.strategy_profiles import STRATEGY_CONFIGS
from modules.line_bot import send_line_bot_message

def analyze_stocks_with_signals(mode="opening", limit=None, min_score=None, include_weak=None):
    config = STRATEGY_CONFIGS.get(mode, STRATEGY_CONFIGS["opening"])
    limit = limit if limit is not None else config["limit"]
    min_score = min_score if min_score is not None else config["min_score"]
    include_weak = include_weak if include_weak is not None else config["include_weak"]
    weights = config.get("weights", {})

    print(f"[signal] 分析模式：{mode} | 掃描檔數：{limit} | 最低分數：{min_score}")

    try:
        top_stocks = get_top_stocks(limit)
    except Exception as e:
        print(f"[price_fetcher] ❌ 資料解析失敗：{e}")
        top_stocks = []

    if not top_stocks:
        print("[signal] 取得 0 檔股票進行分析")
        return

    eps_data, dividend_data = get_eps_and_dividend()
    print(f"[EPS] ✅ 成功匯入 EPS 資料筆數：{len(eps_data)}")
    print(f"[Dividend] ✅ 成功匯入股利資料筆數：{len(dividend_data)}")

    results = []
    for stock_id in top_stocks:
        result = analyze_technical_indicators(stock_id, eps_data, dividend_data, weights)
        if result:
            results.append(result)

    recommended = [r for r in results if r["score"] >= min_score]
    fallback = sorted(results, key=lambda x: x["score"], reverse=True)[:3]

    if recommended:
        message = f"[{mode.upper()} 推薦股票]\n"
        for r in recommended:
            message += f"{r['stock_id']} | 分數：{r['score']} | 建議：{r['suggestion']}\n"
    else:
        message = f"[{mode.upper()} 無推薦股，回傳觀察股]\n"
        for r in fallback:
            message += f"{r['stock_id']} | 分數：{r['score']} | 建議：{r['suggestion']}\n"

    try:
        send_line_bot_message(message)
    except Exception as e:
        print(f"[LINE BOT] ❌ 推播失敗：{e}")
    else:
        print("[LINE BOT] ✅ 推播成功")

    return recommended or fallback