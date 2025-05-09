# modules/signal_analysis.py

import pandas as pd
from modules.price_fetcher import fetch_price_data
from modules.eps_dividend_scraper import fetch_eps_dividend_data
from modules.fundamental_scraper import fetch_fundamental_data
from modules.ta_generator import generate_technical_signals
from modules.ta_analysis import calculate_technical_scores
from modules.market_sentiment import get_market_sentiment
from modules.strategy_profiles import get_strategy_profile

def analyze_stocks_with_signals(mode="opening"):
    print("[signal_analysis] ✅ 開始整合分析流程...")
    strategy = get_strategy_profile(mode)

    min_turnover = 40_000_000
    price_limit = strategy["price_limit"]
    eps_limit = strategy["eps_limit"]
    min_score = strategy["min_score"]
    recommend_min = int(strategy["recommend_min"])
    recommend_max = int(strategy["recommend_max"])
    fallback_top_n = int(strategy.get("fallback_top_n", 5))

    # Step 1: 取得熱門股清單
    print("[signal_analysis] ⏳ 擷取熱門股清單...")
    price_df = fetch_price_data(min_turnover=min_turnover, limit=price_limit, mode=mode, strategy=strategy)
    if price_df.empty:
        print("[signal_analysis] ⚠️ 熱門股清單為空，終止分析")
        return pd.DataFrame()
    stock_ids = price_df["stock_id"].tolist()
    print(f"[signal_analysis] 🔍 共擷取到 {len(stock_ids)} 檔熱門股")

    # Step 2: EPS、殖利率資料
    print(f"[signal_analysis] ⏳ 擷取 EPS 與殖利率資料（最多 {eps_limit} 檔）...")
    eps_df = fetch_eps_dividend_data(stock_ids, limit=eps_limit)

    # Step 3: 法人買超
    print("[signal_analysis] ⏳ 擷取法人買賣超資料...")
    fund_df = fetch_fundamental_data()

    # Step 4: 合併資料
    print("[signal_analysis] 🔧 合併所有來源資料...")
    df = price_df.merge(eps_df, on="stock_id", how="left") \
                 .merge(fund_df, on="stock_id", how="left")

    # Step 5: 計算技術指標欄位
    print("[signal_analysis] ⚙️ 產生技術指標欄位...")
    df = generate_technical_signals(df)

    # Step 6: 市場氣氛加權（如有）
    if strategy.get("apply_sentiment_adjustment", False):
        sentiment = get_market_sentiment()
        factor = 1.0
        if sentiment["status"] == "正向":
            factor = 1.1
        elif sentiment["status"] == "負向":
            factor = 0.9
        print(f"[signal_analysis] 📈 市場氣氛：{sentiment['note']} ➜ 分數乘以 {factor}")
    else:
        factor = 1.0

    # Step 7: 評分與建議
    print("[signal_analysis] 📊 計算技術分數與投資建議...")
    scored_df = calculate_technical_scores(df, **strategy)
    scored_df["score"] = scored_df["score"] * factor
    scored_df["score"] = scored_df["score"].clip(upper=strategy.get("limit_score", 10.0))

    # Step 8: 走弱股（若啟用）
    weak_stocks = scored_df[(df.get("weak_signal", 0) >= 1)]
    weak_stocks = weak_stocks.sort_values(by="score").head(3)
    weak_stocks["label"] = "⚠️ 走弱股"

    # Step 9: 推薦股與觀察股
    top_candidates = scored_df.sort_values(by="score", ascending=False)
    recommended = top_candidates[top_candidates["score"] >= min_score].head(recommend_max)
    fallback = top_candidates.head(fallback_top_n)

    if not recommended.empty:
        recommended["label"] = "✅ 推薦股"
        result = pd.concat([recommended, weak_stocks], ignore_index=True)
        print(f"[signal_analysis] ✅ 推薦股票完成，共 {len(recommended)} 檔 + 弱勢股 {len(weak_stocks)} 檔")
        return result
    else:
        fallback["label"] = "👀 觀察股"
        result = pd.concat([fallback, weak_stocks], ignore_index=True)
        print("[signal_analysis] ⚠️ 無推薦股票，顯示觀察股供參考")
        return result