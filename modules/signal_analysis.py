import pandas as pd
from modules.ta_analysis import calculate_technical_scores
from modules.price_fetcher import fetch_price_data
from modules.eps_dividend_scraper import fetch_eps_dividend_data
from modules.fundamental_scraper import fetch_fundamental_data

def analyze_stocks_with_signals(min_turnover=50_000_000, min_score=5, limit=100, fallback_top_n=5):
    print("[signal_analysis] ✅ 開始整合分析流程...")

    # Step 1：擷取熱門股價資料
    print("[signal_analysis] ⏳ 擷取熱門股清單...")
    price_df = fetch_price_data(min_turnover=min_turnover, limit=limit)
    if price_df.empty:
        print("[signal_analysis] ⚠️ 熱門股清單為空，終止分析")
        return pd.DataFrame()

    stock_ids = price_df['stock_id'].tolist()
    print(f"[signal_analysis] 🔍 共擷取到 {len(stock_ids)} 檔熱門股")

    # Step 2：基本面資料（EPS / 殖利率 / YTD）
    print(f"[signal_analysis] ⏳ 擷取 EPS 與殖利率資料（最多 20 檔）...")
    eps_df = fetch_eps_dividend_data(stock_ids, limit=20)

    # Step 3：法人籌碼資料（加入容錯）
    print("[signal_analysis] ⏳ 擷取法人買賣超資料...")
    try:
        fund_df = fetch_fundamental_data()
    except Exception as e:
        print(f"[signal_analysis] ⚠️ 法人資料擷取失敗，自動跳過：{e}")
        fund_df = pd.DataFrame(columns=["stock_id", "buy_total"])

    # Step 4：合併所有資料
    print("[signal_analysis] 🔧 合併所有來源資料...")
    df = price_df.merge(eps_df, on="stock_id", how="left") \
                 .merge(fund_df, on="stock_id", how="left")

    # Step 5：補齊缺失值
    df["eps_growth"] = df["eps_growth"].fillna(False)
    df["dividend_yield"] = df["dividend_yield"].fillna(0.0)
    df["ytd_return"] = df["ytd_return"].fillna(0.0)
    df["buy_total"] = df["buy_total"].fillna(0)

    # Step 6：技術評分與建議
    print("[signal_analysis] 📊 計算技術分數與投資建議...")
    final_df = calculate_technical_scores(df)

    # Step 7：選出推薦股票
    recommended = final_df[final_df['score'] >= min_score].copy()
    recommended = recommended.sort_values(by="score", ascending=False).reset_index(drop=True)

    if not recommended.empty:
        print(f"[signal_analysis] ✅ 推薦股票完成，共 {len(recommended)} 檔符合條件")
        return recommended

    # Step 8：無推薦股票 → 顯示觀察股 fallback
    print(f"[signal_analysis] ⚠️ 無推薦股票，顯示前 {fallback_top_n} 檔觀察股供參考")
    fallback = final_df.sort_values(by="score", ascending=False).head(fallback_top_n).reset_index(drop=True)
    return fallback
