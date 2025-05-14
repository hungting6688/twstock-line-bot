print("[signal_analysis] ✅ 已載入最新版 (with get_top_stocks)")

from modules.price_fetcher import fetch_price_data
from modules.ta_generator import generate_ta_signals
from modules.eps_dividend_scraper import fetch_eps_dividend_data
from modules.fundamental_scraper import fetch_fundamental_data
from modules.strategy_profiles import get_strategy_profile
from modules.market_sentiment import get_market_sentiment_adjustments

import pandas as pd

def analyze_stocks_with_signals(mode="opening", **kwargs):
    print(f"[signal_analysis] ✅ 開始整合分析流程（策略：{mode}）...")
    try:
        strategy = get_strategy_profile(mode)
        limit = kwargs.get("limit", strategy.get("limit", 100))
        min_score = kwargs.get("min_score", strategy.get("min_score", 7))
        include_weak = kwargs.get("include_weak", strategy.get("include_weak", False))

        price_df = fetch_price_data(limit=limit)
        if price_df is None or price_df.empty:
            print("[signal_analysis] ❌ 無法取得股價資料")
            return None

        stock_ids = price_df["證券代號"].astype(str).tolist()
        ta_df = generate_ta_signals(stock_ids)
        eps_df = fetch_eps_dividend_data(stock_ids, max_count=limit)
        fund_df = fetch_fundamental_data(stock_ids)
        sentiment_weights = get_market_sentiment_adjustments()

        df = price_df.merge(ta_df, on="證券代號", how="left")
        df = df.merge(eps_df, on="證券代號", how="left")
        df = df.merge(fund_df, on="證券代號", how="left")

        scored = []
        for _, row in df.iterrows():
            score = 0
            reasons = []

            def add_score(cond, pts, desc):
                nonlocal score
                if cond:
                    score += pts
                    reasons.append(desc)

            add_score(row.get("MACD", 0) == 1, strategy["weights"].get("MACD", 1), "MACD 黃金交叉")
            add_score(row.get("K", 0) > row.get("D", 0), strategy["weights"].get("KD", 1), "KD 黃金交叉")
            add_score(row.get("RSI", 0) >= 50, strategy["weights"].get("RSI", 1), "RSI 強勢")
            add_score(row.get("均線", 0) == 1, strategy["weights"].get("MA", 1), "短期均線偏多")
            add_score(row.get("布林通道", 0) == 1, strategy["weights"].get("BB", 1), "布林通道突破")

            add_score(row.get("殖利率", 0) >= 5, strategy["weights"].get("dividend", 1), "高殖利率")
            add_score(row.get("EPS", 0) >= 5, strategy["weights"].get("eps", 1), "EPS 穩健")
            add_score(row.get("PE", 999) <= 15, strategy["weights"].get("pe", 1), "本益比合理")
            add_score(row.get("ROE", 0) >= 10, strategy["weights"].get("roe", 1), "ROE 佳")

            # 加入市場情緒調整權重
            score *= sentiment_weights.get("adjust", 1.0)

            label = "✅ 推薦" if score >= min_score else "📌 觀察"
            if include_weak and row.get("RSI", 0) < 30:
                label = "⚠️ 走弱"

            name = row.get("證券名稱", "")
            scored.append({
                "stock_id": row["證券代號"],
                "name": name,
                "score": round(score, 2),
                "label": label,
                "reasons": "、".join(reasons)
            })

        scored = sorted(scored, key=lambda x: x["score"], reverse=True)
        top_recommend = [s for s in scored if s["label"] == "✅ 推薦"][:8]

        if not top_recommend:
            fallback = scored[:3]
            for f in fallback:
                f["label"] = "📌 觀察"
            return fallback

        return top_recommend + [s for s in scored if s["label"] != "✅ 推薦"][:3]

    except Exception as e:
        print(f"[signal_analysis] ❌ 分析失敗：{e}")
        return None
