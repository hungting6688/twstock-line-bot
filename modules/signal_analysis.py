print("[signal_analysis] ✅ 已載入最新版 (with get_top_stocks)")

import pandas as pd
from modules.price_fetcher import fetch_price_data
from modules.ta_generator import generate_ta_signals
from modules.eps_dividend_scraper import fetch_eps_dividend_data
from modules.fundamental_scraper import fetch_fundamental_data
from modules.strategy_profiles import get_strategy_profile
from modules.market_sentiment import get_market_sentiment_adjustments

def analyze_stocks_with_signals(mode="opening", min_score=7, include_weak=False):
    print(f"[signal_analysis] ✅ 開始整合分析流程（策略：{mode}）...")

    try:
        df = fetch_price_data(mode=mode)
    except Exception as e:
        print(f"[signal_analysis] ⚠️ 發生錯誤：{e}，將以空資料處理")
        return []

    if df is None or df.empty:
        print("[signal_analysis] ⚠️ 無法取得熱門股清單，跳過分析")
        return []

    stock_ids = df["stock_id"].tolist()
    ta_df = generate_ta_signals(stock_ids)
    eps_df = fetch_eps_dividend_data(stock_ids)
    fund_df = fetch_fundamental_data(stock_ids)

    merged = df.merge(ta_df, on="stock_id", how="left")
    merged = merged.merge(eps_df, on="stock_id", how="left")
    merged = merged.merge(fund_df, on="stock_id", how="left")

    merged = merged.fillna(0)
    profile = get_strategy_profile(mode)
    market_weight = get_market_sentiment_adjustments()

    results = []
    for _, row in merged.iterrows():
        score = 0
        reasons = []

        for factor, weight in profile["weights"].items():
            value = row.get(factor, 0)
            adj_weight = weight * market_weight.get(factor, 1.0)
            if isinstance(value, (int, float)) and value > 0:
                score += adj_weight
                reasons.append(f"{factor} +{adj_weight}")

        label = ""
        if score >= min_score:
            label = "✅ 推薦"
        elif include_weak and score <= profile.get("weak_threshold", 2):
            label = "⚠️ 走弱"
        else:
            label = "📌 觀察"

        results.append({
            "stock_id": row["stock_id"],
            "name": row["name"],
            "score": round(score, 2),
            "reasons": ", ".join(reasons),
            "label": label
        })

    results = sorted(results, key=lambda x: -x["score"])
    return results