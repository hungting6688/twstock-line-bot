print("[signal_analysis] ✅ 已載入最新版 (with get_top_stocks)")

import pandas as pd
from modules.price_fetcher import fetch_price_data
from modules.ta_generator import generate_technical_indicators
from modules.eps_dividend_scraper import fetch_eps_dividend_data
from modules.fundamental_scraper import fetch_fundamental_data
from modules.strategy_profiles import get_strategy_profile
from modules.market_sentiment import get_market_sentiment_score


def analyze_stocks_with_signals(mode="default", limit=100, min_score=7, include_weak=False):
    print(f"[signal_analysis] ✅ 開始整合分析流程（策略：{mode}）...")

    try:
        price_df = fetch_price_data(limit=limit)
        if not isinstance(price_df, pd.DataFrame) or price_df.empty:
            raise ValueError("取得的股價資料無效，啟動 fallback 模式")
    except Exception as e:
        print(f"[signal_analysis] ⚠️ 發生錯誤：{e}，將以空資料處理")
        return []

    try:
        stock_ids = price_df["stock_id"].tolist()
        price_df = generate_technical_indicators(price_df)
        eps_df = fetch_eps_dividend_data(stock_ids)
        fund_df = fetch_fundamental_data(stock_ids)
    except Exception as e:
        print(f"[signal_analysis] ⚠️ 資料擴充過程失敗：{e}")
        return []

    # 合併所有資料
    try:
        merged = price_df.merge(eps_df, on="stock_id", how="left")
        merged = merged.merge(fund_df, on="stock_id", how="left")
    except Exception as e:
        print(f"[signal_analysis] ❌ 資料合併失敗：{e}")
        return []

    # 欄位補值處理
    merged.fillna(0, inplace=True)

    # 套用策略與評分機制
    strategy = get_strategy_profile(mode)
    sentiment_score = get_market_sentiment_score()

    def score_row(row):
        score = 0
        reasons = []
        for key, weight in strategy["weights"].items():
            value = row.get(key, 0)
            if isinstance(value, (int, float)) and value:
                score += weight
                reasons.append(f"{key}")
        # 根據市場情緒加分
        score += sentiment_score * strategy.get("sentiment_weight", 0)
        return round(score, 1), reasons

    results = []
    for _, row in merged.iterrows():
        score, reasons = score_row(row)
        label = ""
        if score >= min_score:
            label = "✅ 推薦"
        elif include_weak and score <= 3:
            label = "⚠️ 走弱"
        else:
            label = "📌 觀察"

        results.append({
            "stock_id": row["stock_id"],
            "name": row["name"],
            "score": score,
            "label": label,
            "reasons": reasons
        })

    print(f"[signal_analysis] ✅ 分析完成，共 {len(results)} 檔")
    return results
