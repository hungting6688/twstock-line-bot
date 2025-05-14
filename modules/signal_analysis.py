print("[signal_analysis] ✅ 已載入最新版 (with get_top_stocks)")

import pandas as pd
from modules.price_fetcher import fetch_price_data
from modules.ta_generator import generate_ta_signals
from modules.eps_dividend_scraper import fetch_eps_dividend_data
from modules.fundamental_scraper import fetch_fundamental_data
from modules.strategy_profiles import get_strategy_profile
from modules.market_sentiment import get_market_sentiment_score

def analyze_stocks_with_signals(mode="opening", include_weak=False, **kwargs):
    print(f"[signal_analysis] ✅ 開始整合分析流程（策略：{mode}）...")

    try:
        strategy = get_strategy_profile(mode)
        limit = strategy.get("limit", 100)
        min_score = strategy.get("min_score", 7)
        weight = strategy.get("weights", {})
    except Exception as e:
        print(f"[signal_analysis] ⚠️ 策略載入失敗：{e}")
        return []

    try:
        df_price = fetch_price_data(limit=limit)
        if df_price.empty:
            raise ValueError("取得的股價資料無效")
    except Exception as e:
        print(f"[signal_analysis] ⚠️ 發生錯誤：{e}，將以空資料處理")
        return []

    try:
        df_ta = generate_ta_signals(df_price["stock_id"].tolist())
        df_eps = fetch_eps_dividend_data(df_price["stock_id"].tolist())
        df_fund = fetch_fundamental_data(df_price["stock_id"].tolist())

        # 合併所有資料
        df = df_price.merge(df_ta, on="stock_id", how="left")
        df = df.merge(df_eps, on="stock_id", how="left")
        df = df.merge(df_fund, on="stock_id", how="left")

        df["score"] = 0

        for col, w in weight.items():
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
                df["score"] += df[col] * w

        sentiment = get_market_sentiment_score()
        df["score"] *= 1 + (sentiment - 5) / 20

        df["score"] = df["score"].round(1)
        df["label"] = df["score"].apply(lambda s: "✅ 推薦" if s >= min_score else "")
        df.loc[(df["score"] < min_score) & (include_weak), "label"] = "📌 觀察"

        df_result = df[df["label"] != ""].sort_values("score", ascending=False)

        # fallback：若無推薦，挑前幾名也列為觀察
        if df_result.empty:
            fallback_df = df.sort_values("score", ascending=False).head(5).copy()
            fallback_df["label"] = "📌 觀察"
            df_result = fallback_df

        result = df_result[["stock_id", "name", "score", "label"]].to_dict("records")
        print(f"[signal_analysis] ✅ 分析完成，共 {len(result)} 檔符合條件")
        return result

    except Exception as e:
        print(f"[signal_analysis] ❌ 分析過程失敗：{e}")
        return []