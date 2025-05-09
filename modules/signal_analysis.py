import pandas as pd
from modules.ta_analysis import calculate_technical_scores
from modules.ta_generator import generate_technical_signals
from modules.price_fetcher import fetch_price_data
from modules.eps_dividend_scraper import fetch_eps_dividend_data
from modules.fundamental_scraper import fetch_fundamental_data
from modules.strategy_profiles import get_strategy_profile
from modules.market_sentiment import get_market_sentiment  # 可選擇性引入

def analyze_stocks_with_signals(mode="opening"):
    print("[signal_analysis] ✅ 開始整合分析流程...")

    strategy = get_strategy_profile(mode)
    min_turnover = 40_000_000
    min_score = strategy["min_score"]
    price_limit = strategy["price_limit"]
    eps_limit = strategy["eps_limit"]
    recommend_min = int(strategy["recommend_min"])
    recommend_max = int(strategy.get("recommend_max", 8))
    apply_sentiment = strategy.get("apply_sentiment_adjustment", False)

    # Step 1：熱門股擷取
    print("[signal_analysis] ⏳ 擷取熱門股清單...")
    price_df = fetch_price_data(min_turnover=min_turnover, limit=price_limit)
    if price_df.empty:
        print("[signal_analysis] ⚠️ 熱門股清單為空，終止分析")
        return pd.DataFrame()

    stock_ids = price_df["stock_id"].tolist()
    print(f"[signal_analysis] 🔍 共擷取到 {len(stock_ids)} 檔熱門股")

    # Step 2：基本面資料擷取
    print(f"[signal_analysis] ⏳ 擷取 EPS 與殖利率資料（最多 {eps_limit} 檔）...")
    eps_df = fetch_eps_dividend_data(stock_ids, limit=eps_limit)

    print("[signal_analysis] ⏳ 擷取法人買賣超資料...")
    fund_df = fetch_fundamental_data()

    # Step 3：資料合併
    print("[signal_analysis] 🔧 合併所有來源資料...")
    df = price_df.merge(eps_df, on="stock_id", how="left") \
                 .merge(fund_df, on="stock_id", how="left")

    # Step 4：技術指標產生
    print("[signal_analysis] ⚙️ 產生技術指標欄位...")
    df = generate_technical_signals(df)

    # Step 5：市場情緒評估（若啟用）
    sentiment_multiplier = 1.0
    if apply_sentiment:
        sentiment = get_market_sentiment()
        sentiment_multiplier = {
            1: 1.1,
            0: 1.0,
           -1: 0.9
        }.get(sentiment["sentiment_score"], 1.0)
        print(f"[signal_analysis] 📈 市場氣氛：{sentiment['note']} ➜ 分數乘以 {sentiment_multiplier}")

    # Step 6：評分
    print("[signal_analysis] 📊 計算技術分數與投資建議...")
    scored_df = calculate_technical_scores(df, **strategy)

    # Step 7：乘上市場氣氛倍率（如有）
    scored_df["score"] = scored_df["score"] * sentiment_multiplier
    scored_df["score"] = scored_df["score"].round(2)

    # Step 8：推薦股過濾
    recommended = scored_df[scored_df["score"] >= min_score] \
        .sort_values(by="score", ascending=False).head(recommend_max).reset_index(drop=True)

    if not recommended.empty:
        recommended["label"] = "✅ 推薦股"
        print(f"[signal_analysis] ✅ 推薦股票完成，共 {len(recommended)} 檔")

    # Step 9：無推薦 fallback → 顯示觀察股
    else:
        recommended = scored_df.sort_values(by="score", ascending=False).head(recommend_min).reset_index(drop=True)
        recommended["label"] = "👀 觀察股"
        print("[signal_analysis] ⚠️ 無推薦股票，顯示觀察股供參考")

    return recommended
