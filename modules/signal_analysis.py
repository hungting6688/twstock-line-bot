print("[signal_analysis] ✅ 已載入最新版")

from modules.ta_analysis import analyze_technical_indicators
from modules.price_fetcher import get_realtime_top_stocks
from modules.eps_dividend_scraper import get_eps_data
from modules.strategy_profiles import STRATEGY_CONFIGS

def analyze_stocks_with_signals(
    mode="opening",
    limit=None,
    min_score=None,
    include_weak=False
):
    print(f"[signal] 分析模式：{mode} | 掃描檔數：{limit} | 最低分數：{min_score}")

    try:
        stock_list = get_realtime_top_stocks(limit or 100)
    except Exception as e:
        print(f"[signal] 取得熱門股失敗：{e}")
        stock_list = []

    print(f"[signal] 取得 {len(stock_list)} 檔股票進行分析")

    eps_data = get_eps_data()
    print(f"[EPS] ✅ 成功匯入 EPS 資料筆數：{len(eps_data)}")
    print(f"[Dividend] ✅ 成功匯入股利資料筆數：{len([v for v in eps_data.values() if v.get('dividend')])}")

    config = STRATEGY_CONFIGS.get(mode, STRATEGY_CONFIGS["default"])
    results = []

    for sid in stock_list:
        try:
            result = analyze_technical_indicators(
                stock_id=sid,
                eps=eps_data.get(sid, {}).get("eps"),
                dividend=eps_data.get(sid, {}).get("dividend"),
                weights=config["weights"],
                suggest_text=True
            )
            if result:
                results.append(result)
        except Exception as e:
            print(f"[ta_analysis] {sid} 分析失敗：{e}")

    # 排除極弱股除非指定 include_weak=True
    if not include_weak:
        results = [r for r in results if not r.get("is_weak")]

    # 推薦條件篩選與排序
    recommended = [r for r in results if r["score"] >= (min_score or config["min_score"])]
    recommended = sorted(recommended, key=lambda x: x["score"], reverse=True)

    # 若無推薦股，回傳最高分觀察股 2~3 檔 fallback
    if not recommended:
        fallback = sorted(results, key=lambda x: x["score"], reverse=True)[:3]
        print("[signal] 無推薦股，回傳觀察股")
        return fallback

    return recommended