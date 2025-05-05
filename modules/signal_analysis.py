# modules/signal_analysis.py

from modules.price_fetcher import fetch_price_data
from modules.ta_analysis import analyze_signals
from modules.eps_dividend_scraper import fetch_eps_dividend_data
from modules.stock_data_utils import get_latest_valid_trading_date
import datetime

def analyze_stocks_with_signals(
    title="📈 股票推薦分析",
    stock_ids=None,
    limit=100,
    min_score=2.0,
    include_weak=True,
    filter_type="all",
    date=None
):
    msg = f"{title}\n"
    date = date or get_latest_valid_trading_date()
    eps_df = fetch_eps_dividend_data()

    if stock_ids is None:
        from modules.stock_data_utils import get_all_stock_ids
        stock_ids = get_all_stock_ids(limit=limit, filter_type=filter_type)

    all_results = []
    for stock_id in stock_ids:
        price_data = fetch_price_data(stock_id, end=date)
        if price_data is None or price_data.empty:
            continue

        eps = eps_df[eps_df["stock_id"] == stock_id]["eps"].mean() if stock_id in eps_df["stock_id"].values else None
        result = analyze_signals(stock_id, price_data, eps)
        if result:
            all_results.append(result)

    if not all_results:
        return msg + "\n⚠️ 今日無法取得任何分析資料。"

    # 推薦股與觀察股分組
    recommended = [r for r in all_results if r["score"] >= min_score]
    observed = sorted([r for r in all_results if r["score"] < min_score], key=lambda x: x["score"], reverse=True)[:3]
    weak_alerts = [r for r in all_results if r["is_weak"]]

    if recommended:
        msg += "\n✅ **推薦股（高分排序）**\n"
        for r in sorted(recommended, key=lambda x: x["score"], reverse=True):
            msg += f"\n{r['stock_id']} 分數：{r['score']:.1f}\n{r['summary']}"
    else:
        msg += "\n⚠️ 今日無符合推薦門檻的股票。\n"

    if observed:
        msg += "\n📌 **觀察股（次高分）**\n"
        for r in observed:
            msg += f"\n{r['stock_id']} 分數：{r['score']:.1f}\n{r['summary']}"

    if include_weak and weak_alerts:
        msg += "\n⚠️ **極弱警示股（走勢偏弱）**\n"
        for r in weak_alerts:
            msg += f"\n{r['stock_id']}（極弱警示）"

    return msg.strip()
