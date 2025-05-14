# modules/signal_analysis.py
print("[signal_analysis] ✅ 已載入最新版 (with get_top_stocks)")

import pandas as pd
from modules.price_fetcher import fetch_price_data
from modules.ta_generator import generate_ta_signals
from modules.eps_dividend_scraper import fetch_eps_dividend_data
from modules.fundamental_scraper import fetch_fundamental_data
from modules.market_sentiment import get_market_sentiment_score
from modules.strategy_profiles import strategy_profiles

def analyze_stocks_with_signals(strategy_name="default", **kwargs):
    print(f"[signal_analysis] ✅ 開始整合分析流程（策略：{strategy_name}）...")
    profile = strategy_profiles.get(strategy_name, strategy_profiles["default"])
    profile.update(kwargs)

    stock_data = fetch_price_data()
    if stock_data.empty:
        print("[signal_analysis] ❌ 無法取得股價資料")
        return {"recommended": [], "watchlist": [], "weak": []}

    stock_ids = stock_data["證券代號"].tolist()
    ta_signals = generate_ta_signals(stock_ids)
    eps_data = fetch_eps_dividend_data(stock_ids)
    fundamental_data = fetch_fundamental_data(stock_ids)

    df = stock_data.merge(ta_signals, on="證券代號", how="left")
    df = df.merge(eps_data, on="證券代號", how="left")
    df = df.merge(fundamental_data, on="證券代號", how="left")

    weights = profile["weights"]
    for key in weights:
        df[key] = pd.to_numeric(df[key], errors="coerce").fillna(0)

    df["score"] = sum(df[key] * weight for key, weight in weights.items())

    # 市場情緒加權
    sentiment_score = get_market_sentiment_score()
    df["score"] += sentiment_score * profile.get("sentiment_boost_weight", 0)

    # 小型股 or 大型股條件篩選
    if profile.get("filter_type") == "small_cap":
        df = df[df["成交金額"] < 5e8]
    elif profile.get("filter_type") == "large_cap":
        df = df[df["成交金額"] >= 5e8]

    df = df.sort_values("score", ascending=False)

    recommended = df[df["score"] >= profile["min_score"]].head(profile["max_recommend"])
    fallback = df.head(20)

    result = {
        "recommended": [],
        "watchlist": [],
        "weak": [],
    }

    seen = set()
    for _, row in pd.concat([recommended, fallback]).iterrows():
        sid = row["證券代號"]
        if sid in seen:
            continue
        seen.add(sid)

        item = {
            "stock_id": sid,
            "name": row["證券名稱"],
            "score": round(row["score"], 1),
            "reason": explain_reasons(row, weights),
            "suggestion": get_suggestion(row["score"]),
        }

        if row["score"] >= profile["min_score"]:
            result["recommended"].append(item)
        else:
            result["watchlist"].append(item)

    if profile.get("include_weak"):
        weak_df = df[df["score"] <= 1].sort_values("score").head(2)
        for _, row in weak_df.iterrows():
            result["weak"].append({
                "stock_id": row["證券代號"],
                "name": row["證券名稱"],
                "score": round(row["score"], 1),
                "reason": "綜合評分過低，請留意走弱風險"
            })

    return result

def explain_reasons(row, weights):
    reasons = []
    if "MACD" in weights and row["MACD"] > 0:
        reasons.append("MACD 黃金交叉")
    if "K" in weights and row["K"] > row["D"]:
        reasons.append("KD 黃金交叉")
    if "RSI" in weights and row["RSI"] > 50:
        reasons.append("RSI 走強")
    if "均線" in weights and row["均線"] > 0:
        reasons.append("站上均線")
    if "布林通道" in weights and row["布林通道"] > 0:
        reasons.append("布林通道偏多")
    if "殖利率" in weights and row["殖利率"] > 4:
        reasons.append("高殖利率")
    if "EPS_YOY" in weights and row["EPS_YOY"] > 0:
        reasons.append("EPS 成長")
    if "buy_total" in weights and row["buy_total"] > 0:
        reasons.append("法人買超")

    return "、".join(reasons) if reasons else "綜合表現"

def get_suggestion(score):
    if score >= 9:
        return "建議立即列入關注清單"
    elif score >= 7:
        return "建議密切觀察"
    elif score >= 5:
        return "建議暫不進場"
    else:
        return "不建議操作"
