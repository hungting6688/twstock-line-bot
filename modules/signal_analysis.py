# ✅ signal_analysis.py（整合推薦股、觀察股、走弱股）
import pandas as pd
from modules.ta_analysis import calculate_technical_scores
from modules.ta_generator import generate_technical_signals
from modules.price_fetcher import fetch_price_data
from modules.eps_dividend_scraper import fetch_eps_dividend_data
from modules.fundamental_scraper import fetch_fundamental_data
from modules.strategy_profiles import get_strategy_profile

def analyze_stocks_with_signals(mode="opening"):
    print("[signal_analysis] ✅ 開始整合分析流程...")

    strategy = get_strategy_profile(mode)
    min_turnover = 40_000_000
    min_score = strategy["min_score"]
    price_limit = strategy["price_limit"]
    eps_limit = strategy["eps_limit"]
    recommend_min = int(strategy["recommend_min"])
    recommend_max = int(strategy.get("recommend_max", 8))
    weak_threshold = strategy.get("weak_threshold", 2)

    # Step 1：股價與成交金額
    print("[signal_analysis] ⏳ 擷取熱門股清單...")
    price_df = fetch_price_data(min_turnover=min_turnover, limit=price_limit, mode=mode, strategy=strategy)
    if price_df.empty:
        print("[signal_analysis] ⚠️ 熱門股清單為空，終止分析")
        return {}

    stock_ids = price_df["stock_id"].tolist()
    print(f"[signal_analysis] 🔍 共擷取到 {len(stock_ids)} 檔熱門股")

    # Step 2：EPS 與殖利率
    print(f"[signal_analysis] ⏳ 擷取 EPS 與殖利率資料（最多 {eps_limit} 檔）...")
    eps_df = fetch_eps_dividend_data(stock_ids, limit=eps_limit)

    # Step 3：法人籌碼
    print("[signal_analysis] ⏳ 擷取法人買賣超資料...")
    fund_df = fetch_fundamental_data()

    # Step 4：資料合併
    print("[signal_analysis] 🔧 合併所有來源資料...")
    df = price_df.merge(eps_df, on="stock_id", how="left") \
                 .merge(fund_df, on="stock_id", how="left")

    # Step 5：技術指標欄位
    print("[signal_analysis] ⚙️ 產生技術指標欄位...")
    df = generate_technical_signals(df)

    # Step 6：評分與建議
    print("[signal_analysis] 📊 計算技術分數與投資建議...")
    scored_df = calculate_technical_scores(df, **strategy)

    # Step 7：推薦股選出
    recommended = scored_df[scored_df["score"] >= min_score] \
        .sort_values(by="score", ascending=False).head(recommend_max).reset_index(drop=True)

    # Step 8：Fallback 觀察股
    fallback = scored_df.sort_values(by="score", ascending=False).head(recommend_min).reset_index(drop=True)

    # Step 9：極弱股（符合多項弱勢指標）
    weak_stocks = scored_df[scored_df.get("weak_signal", 0) >= weak_threshold] \
        .sort_values(by="score").head(3).reset_index(drop=True)

    return {
        "recommended": recommended,
        "fallback": fallback,
        "weak": weak_stocks
    }
