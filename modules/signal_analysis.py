# modules/signal_analysis.py

import pandas as pd
from modules.ta_analysis import calculate_technical_scores
from modules.price_fetcher import fetch_price_data
from modules.eps_dividend_scraper import fetch_eps_dividend_data
from modules.fundamental_scraper import fetch_fundamental_data
from modules.ta_generator import generate_ta_signals
from modules.strategy_profiles import get_strategy_profile

def analyze_stocks_with_signals(mode="opening"):
    print("[signal_analysis] ✅ 開始整合分析流程...")
    strategy = get_strategy_profile(mode)

    # Step 1：擷取股價與成交金額
    print("[signal_analysis] ⏳ 擷取熱門股清單...")
    price_df = fetch_price_data(min_turnover=50_000_000, limit=strategy["price_limit"])
    if price_df.empty:
        print("[signal_analysis] ⚠️ 熱門股清單為空，終止分析")
        return pd.DataFrame()

    stock_ids = price_df["stock_id"].tolist()
    print(f"[signal_analysis] 🔍 共擷取到 {len(stock_ids)} 檔熱門股")

    # Step 2：EPS 與殖利率
    print(f"[signal_analysis] ⏳ 擷取 EPS 與殖利率資料（最多 {strategy['eps_limit']} 檔）...")
    eps_df = fetch_eps_dividend_data(stock_ids, limit=strategy["eps_limit"])

    # Step 3：法人籌碼
    print("[signal_analysis] ⏳ 擷取法人買賣超資料...")
    fund_df = fetch_fundamental_data()

    # Step 4：合併資料
    print("[signal_analysis] 🔧 合併所有來源資料...")
    df = price_df.merge(eps_df, on="stock_id", how="left")
    df = df.merge(fund_df, on="stock_id", how="left")

    # Step 5：預處理欄位
    df["eps_growth"] = df["eps_growth"].fillna(False)
    df["dividend_yield"] = df["dividend_yield"].fillna(0.0)
    df["ytd_return"] = df["ytd_return"].fillna(0.0)
    df["buy_total"] = df["buy_total"].fillna(0)

    # Step 6：產生技術指標欄位
    print("[signal_analysis] ⚙️ 產生技術指標欄位...")
    df = generate_ta_signals(df)

    # Step 7：評分
    print("[signal_analysis] 📊 計算技術分數與投資建議...")
    final_df = calculate_technical_scores(df, mode=mode)

    # Step 8：推薦股票
    recommended = final_df[final_df["score"] >= strategy["min_score"]] \
        .sort_values(by="score", ascending=False) \
        .reset_index(drop=True)

    if not recommended.empty:
        print(f"[signal_analysis] ✅ 推薦股票完成，共 {len(recommended)} 檔符合條件")
        return recommended

    # fallback
    fallback = final_df.sort_values(by="score", ascending=False).head(5).reset_index(drop=True)
    print("[signal_analysis] ⚠️ 無推薦股票，顯示前 5 檔觀察股供參考")
    return fallback
