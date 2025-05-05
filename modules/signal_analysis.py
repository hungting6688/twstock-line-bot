# modules/signal_analysis.py

from modules.stock_data_utils import get_latest_valid_trading_date, get_hot_stock_ids
from modules.price_fetcher import fetch_price_data
from modules.ta_analysis import analyze_technical_indicators
from modules.eps_dividend_scraper import fetch_eps_dividend_info

def analyze_stocks_with_signals(
    title="📈 股票分析報告",
    limit=100,
    min_score=2.0,
    filter_type="all"
):
    date = get_latest_valid_trading_date()
    stock_ids = get_hot_stock_ids(limit=limit, filter_type=filter_type)

    results = []
    eps_info = fetch_eps_dividend_info()

    for stock_id in stock_ids:
        try:
            price_df = fetch_price_data(stock_id)
            if price_df is None or price_df.empty:
                print(f"⚠️ 無法取得 {stock_id} 價格資料")
                continue

            signals, score = analyze_technical_indicators(price_df)
            eps_data = eps_info.get(stock_id, {})
            explanations = []

            # EPS 條件加分
            eps = eps_data.get("EPS", 0)
            if eps and eps > 2:
                score += 0.5
                explanations.append("🔵 EPS 高於 2，基本面穩定")

            # 殖利率條件加分
            dividend_yield = eps_data.get("殖利率", 0)
            if dividend_yield and dividend_yield > 4:
                score += 0.5
                explanations.append(f"🔵 殖利率 {dividend_yield}% 吸引人")

            # 法人條件加分
            if eps_data.get("法人連買", False):
                score += 0.5
                explanations.append("🟣 法人連續買超，籌碼穩定")

            # 極弱股提醒：符合 MACD 死亡交叉或 RSI > 70
            weak_signals = []
            if "🔻 MACD 死亡交叉，趨勢轉弱" in signals:
                weak_signals.append("MACD 死亡交叉")
            if "🔻 RSI > 70 過熱區，提防拉回" in signals:
                weak_signals.append("RSI 高檔")

            result = {
                "stock_id": stock_id,
                "score": round(score, 2),
                "signals": signals,
                "explanations": explanations,
                "weak_signals": weak_signals,
                "name": eps_data.get("name", "")
            }
            results.append(result)

        except Exception as e:
            print(f"⚠️ 分析 {stock_id} 發生錯誤：{e}")
            continue

    if not results:
        return f"{title}\n⚠️ 今日無法取得任何分析資料。"

    # 分數排序
    sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)

    # 篩出符合推薦分數門檻的股票
    recommended = [r for r in sorted_results if r["score"] >= min_score]
    top_candidates = sorted_results[:3]

    msg = f"{title}\n"

    if recommended:
        msg += "\n✅ 今日推薦股（分數 ≥ " + str(min_score) + "）\n"
        for r in recommended:
            name_part = f"{r['name']} ({r['stock_id']})" if r['name'] else r['stock_id']
            msg += f"\n🔹 {name_part}｜分數：{r['score']}\n"
            for s in r["signals"]:
                msg += f"　• {s}\n"
            for e in r["explanations"]:
                msg += f"　• {e}\n"
    else:
        msg += "\n⚠️ 今日無推薦股，以下為觀察分數較高者：\n"
        for r in top_candidates:
            name_part = f"{r['name']} ({r['stock_id']})" if r['name'] else r['stock_id']
            msg += f"\n🔸 {name_part}｜分數：{r['score']}\n"
            for s in r["signals"]:
                msg += f"　• {s}\n"
            for e in r["explanations"]:
                msg += f"　• {e}\n"

    # 額外提醒弱勢訊號
    weak_list = [r for r in sorted_results if r["score"] < 1.5 and r["weak_signals"]]
    if weak_list:
        msg += "\n\n⚠️ 極弱訊號股（技術面轉弱，請留意）：\n"
        for r in weak_list[:5]:
            name_part = f"{r['name']} ({r['stock_id']})" if r['name'] else r['stock_id']
            msg += f"\n🚨 {name_part}｜分數：{r['score']}\n"
            for w in r["weak_signals"]:
                msg += f"　• {w}\n"

    return msg.strip()
