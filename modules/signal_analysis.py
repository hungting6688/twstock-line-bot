# signal_analysis.py
import pandas as pd
from ta_analysis import calculate_technical_scores
from price_fetcher import fetch_price_data
from eps_dividend_scraper import fetch_eps_dividend_data
from fundamental_scraper import fetch_fundamental_data

def analyze_stocks_with_signals(min_turnover=50000000, min_score=5):
    print("[signal_analysis] 開始整合分析資料...")

    # Step 1：抓熱門股價與成交金額
    price_df = fetch_price_data(min_turnover=min_turnover)
    stock_ids = price_df['stock_id'].tolist()

    # Step 2：抓 EPS / 殖利率 / YTD 報酬率
    eps_df = fetch_eps_dividend_data(stock_ids)

    # Step 3：抓法人買超
    fund_df = fetch_fundamental_data()

    # Step 4：合併所有資料
    df = price_df.merge(eps_df, on='stock_id', how='left') \
                 .merge(fund_df, on='stock_id', how='left')

    # Step 5：填補缺失
    df['eps_growth'] = df['eps_growth'].fillna(False)
    df['dividend_yield'] = df['dividend_yield'].fillna(0.0)
    df['ytd_return'] = df['ytd_return'].fillna(0.0)
    df['buy_total'] = df['buy_total'].fillna(0)

    # Step 6：技術指標計算（已內建技術指標邏輯）
    final_df = calculate_technical_scores(df)

    # Step 7：推薦排序
    recommended = final_df[final_df['score'] >= min_score] \
                    .sort_values(by='score', ascending=False) \
                    .reset_index(drop=True)

    print(f"[signal_analysis] 推薦股票共 {len(recommended)} 檔")
    return recommended