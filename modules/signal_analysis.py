# modules/signal_analysis.py
print("[signal_analysis] ✅ 已載入最新版 (with get_top_stocks)")

import pandas as pd
from modules.price_fetcher import fetch_price_data
from modules.ta_generator import generate_ta_signals
from modules.eps_dividend_scraper import fetch_eps_dividend_data
from modules.fundamental_scraper import fetch_fundamental_data
from modules.market_sentiment import get_market_sentiment_score
from modules.strategy_profiles import strategy_profiles

def analyze_stocks_with_signals(mode="default", **kwargs):
    print(f"[signal_analysis] ✅ 開始整合分析流程（策略：{mode}）...")
    profile = strategy_profiles.get(mode, strategy_profiles["default"])
    profile.update(kwargs)

    stock_data = fetch_price_data(limit=profile["limit"])
    if stock_data.empty:
        print("[signal_analysis] ❌ 無法取得股價資料")
        return []

    stock_ids = stock_data["證券代號"].tolist()
    ta_signals = generate_ta_signals(stock_ids)
    eps_data = fetch_eps_dividend_data(stock_ids)
    fundamental_data = fetch_fundamental_data(stock_ids)

    merged = stock_data.merge(ta_signals, on="證券代號", how="left")
    merged = merged.merge(eps_data, on="證券代號", how="left")
    merged = merged.merge(fundamental_data, on="證券代號", how="left")

    weights = profile["weights"]
    for key in weights:
        merged[key] = merged[key].fillna(0)
        merged[key] = merged[key].astype(float)

    merged["score"] = sum(merged[key] * weight for key, weight in weights.items())

    sentiment_score = get_market_sentiment_score()
    boost = sentiment_score * profile.get("sentiment_boost_weight", 0)
    merged["score"] += boost

    if profile.get("filter_type") == "small_cap":
        merged = merged[merged["成交金額"] < 5e8]
    elif profile.get("filter_type") == "large_cap":
        merged = merged[merged["成交金額"] >= 5e8]

    merged = merged.sort_values("score", ascending=False)

    recommend = merged[merged["score"] >= profile["min_score"]].head(profile["max_recommend"])
    fallback = merged.head(20)

    result = []
    seen = set()
    for _, row in pd.concat([recommend, fallback]).iterrows():
        sid = row["證券代號"]
        if sid in seen:
            continue
        seen.add(sid)
        label = "✅ 推薦" if row["score"] >= profile["min_score"] else "📌 觀察"
        result.append({
            "label": label,
            "stock_id": sid,
            "name": row["證券名稱"],
            "score": round(row["score"], 1),
        })

    if profile.get("include_weak"):
        weak = merged[merged["score"] <= 1].sort_values("score").head(2)
        for _, row in weak.iterrows():
            result.append({
                "label": "⚠️ 走弱",
                "stock_id": row["證券代號"],
                "name": row["證券名稱"],
                "score": round(row["score"], 1),
            })

    return result
