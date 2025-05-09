import pandas as pd
from modules.ta_analysis import calculate_technical_scores
from modules.ta_generator import generate_technical_signals
from modules.price_fetcher import fetch_price_data
from modules.eps_dividend_scraper import fetch_eps_dividend_data
from modules.fundamental_scraper import fetch_fundamental_data
from modules.strategy_profiles import get_strategy_profile

def analyze_stocks_with_signals(mode="opening"):
    print("[signal_analysis] ✅ 開始整合分析流程...")

    # 載入對應時段的策略參數
    strategy = get_strategy_profile(mode)
    min_turnover = 40_000_000
    min_score = strategy.get("min_score", 5)
    price_limit = strategy.get("price_limit", 100)
    eps_limit = strategy.get("eps_limit", 100)
    recommend_min = strategy.get("recommend_min", 5)
    recommend_max = strategy.get("recommend_max", 8)

    # Step 1：擷取熱門股資料
    print("[signal_analysis] ⏳ 擷取熱門股清單...")
    price_df = fetch_price_data(min_turnover=min_turnover, limit=price_limit)
    if price_df.empty:
        print("[signal_analysis] ⚠️ 熱門股清單為空，終止分析")
        return pd.DataFrame()

    stock_ids = price_df['stock_id'].tolist()
    print(f"[signal_analysis] 🔍 共擷取到 {len(stock_ids)} 檔熱門股")

    # Step 2：EPS 與殖利率
    print(f"[signal_analysis] ⏳ 擷取 EPS 與殖利率資料（最多 {eps_limit} 檔）...")
    eps_df = fetch_eps_dividend_data(stock_ids, limit=eps_limit)

    # Step 3：法人買賣超資料
    print("[signal_analysis] ⏳ 擷取法人買賣超資料...")
    fund_df = fetch_fundamental_data()

    # Step 4：資料合併
    print("[signal_analysis] 🔧 合併所有來源資料...")
    df = price_df.merge(eps_df, on="stock_id", how="left") \
                 .merge(fund_df, on="stock_id", how="left")

    # Step 5：產生技術指標欄位
    print("[signal_analysis] ⚙️ 產生技術指標欄位...")
    df = generate_technical_signals(df)

    # Step 6：評分與建議
    print("[signal_analysis] 📊 計算技術分數與投資建議...")
    final_df = calculate_technical_scores(df, strategy=strategy)

    # Step 7：推薦股挑選
    recommended = final_df[final_df["score"] >= min_score] \
        .sort_values(by="score", ascending=False).reset_index(drop=True)

    if not recommended.empty:
        print(f"[signal_analysis] ✅ 推薦股票完成，共 {len(recommended)} 檔")
        return recommended.head(recommend_max)

    # 若無符合推薦門檻，回傳 fallback 觀察股
    fallback = final_df.sort_values(by="score", ascending=False).head(recommend_min).reset_index(drop=True)
    print("[signal_analysis] ⚠️ 無推薦股票，顯示前幾檔觀察股供參考")
    return fallback
