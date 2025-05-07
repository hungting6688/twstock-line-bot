# modules/signal_analysis.py

import pandas as pd
from modules.ta_analysis import calculate_technical_scores
from modules.price_fetcher import fetch_price_data
from modules.eps_dividend_scraper import fetch_eps_dividend_data
from modules.fundamental_scraper import fetch_fundamental_data

def analyze_stocks_with_signals(min_turnover=50_000_000, min_score=5, eps_limit=450, **kwargs):
    print("[signal_analysis] ✅ 開始整合分析流程...")

    # Step 1: 熱門股
    print("[signal_analysis] ⏳ 擇取熱門股清單...")
    price_df = fetch_price_data(min_turnover=min_turnover, limit=eps_limit)
    if price_df.empty:
        print("[signal_analysis] ⚠️ 熱門股清單為空，終止分析")
        return pd.DataFrame()

    stock_ids = price_df['stock_id'].tolist()
    print(f"[signal_analysis] 🔍 共擇取到 {len(stock_ids)} 檫熱門股")

    # Step 2: EPS / 殖利率 / YTD
    print(f"[signal_analysis] ⏳ 擇取 EPS 與殖利率資料（最多 {eps_limit} 檫）...")
    eps_df = fetch_eps_dividend_data(stock_ids, limit=eps_limit)

    # Step 3: 法人資訊
    print("[signal_analysis] ⏳ 擇取法人買賣資料...")
    fund_df = fetch_fundamental_data()

    # Step 4: 合併資料
    print("[signal_analysis] 🔧 合併所有來源資料...")
    df = price_df.merge(eps_df, on='stock_id', how='left')
    if not fund_df.empty:
        df = df.merge(fund_df, on='stock_id', how='left')

    # Step 5: 缺值處理
    df['eps_growth'] = df['eps_growth'].fillna(False)
    df['dividend_yield'] = df['dividend_yield'].fillna(0.0)
    df['ytd_return'] = df['ytd_return'].fillna(0.0)
    df['buy_total'] = df['buy_total'].fillna(0)

    # Step 6: 技術分析與評分
    print("[signal_analysis] 📊 計算技術分數與投資建議...")
    final_df = calculate_technical_scores(df)

    # Step 7: 筛選推薦股
    recommended = final_df[final_df['score'] >= min_score] \
                    .sort_values(by='score', ascending=False) \
                    .reset_index(drop=True)

    if recommended.empty:
        print("[signal_analysis] ⚠️ 無推薦股，顯示前 5 檫觀察股供參考")
        fallback = final_df.sort_values(by='score', ascending=False).head(5).reset_index(drop=True)
        return fallback

    print(f"[signal_analysis] ✅ 推薦股完成，共 {len(recommended)} 檫符合條件")
    return recommended
