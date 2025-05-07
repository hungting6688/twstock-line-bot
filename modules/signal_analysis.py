# modules/signal_analysis.py

import pandas as pd
from modules.price_fetcher import fetch_price_data
from modules.eps_dividend_scraper import fetch_eps_dividend_data
from modules.fundamental_scraper import fetch_fundamental_data
from modules.ta_analysis import calculate_technical_scores

def analyze_stocks_with_signals(
    min_turnover=50_000_000,
    min_score=5,
    eps_limit=200,
    stock_limit=100
):
    print("[signal_analysis] ✅ 開始整合分析流程...")

    # Step 1：擷取熱門股
    print("[signal_analysis] ⏳ 擷取熱門股清單...")
    price_df = fetch_price_data(min_turnover=min_turnover, limit=stock_limit)
    if price_df.empty:
        print("[signal_analysis] ⚠️ 熱門股清單為空，終止分析")
        return pd.DataFrame()

    print(f"[signal_analysis] 🔍 共擷取到 {len(price_df)} 檔熱門股")
    stock_ids = price_df["stock_id"].tolist()

    # Step 2：EPS/殖利率等基本面資料
    print(f"[signal_analysis] ⏳ 擷取 EPS 與殖利率資料（最多 {eps_limit} 檔）...")
    eps_df = fetch_eps_dividend_data(stock_ids, limit=eps_limit)

    # Step 3：法人買超資料
    print("[signal_analysis] ⏳ 擷取法人買賣超資料...")
    fund_df = fetch_fundamental_data()

    # Step 4：資料合併與填補
    print("[signal_analysis] 🔧 合併所有來源資料...")
    df = price_df.merge(eps_df, on="stock_id", how="left") \
                 .merge(fund_df, on="stock_id", how="left")
    df = df.fillna({
        "eps_growth": False,
        "dividend_yield": 0.0,
        "ytd_return": 0.0,
        "buy_total": 0
    })

    # Step 5：技術評分與建議
    print("[signal_analysis] 📊 計算技術分數與投資建議...")
    final_df = calculate_technical_scores(df)

    # Step 6：回傳結果
    recommended = final_df[final_df["score"] >= min_score] \
        .sort_values(by="score", ascending=False) \
        .reset_index(drop=True)

    print(f"[signal_analysis] ✅ 推薦股票完成，共 {len(recommended)} 檔符合條件")
    return recommended
