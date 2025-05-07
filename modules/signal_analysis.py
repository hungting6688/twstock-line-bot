# modules/signal_analysis.py

import pandas as pd
from modules.strategy_profiles import get_strategy_profile
from modules.price_fetcher import fetch_price_data
from modules.ta_generator import generate_ta_signals
from modules.eps_dividend_scraper import fetch_eps_dividend_data
from modules.fundamental_scraper import fetch_fundamental_data
from modules.ta_analysis import calculate_technical_scores

def analyze_stocks_with_signals(mode="opening", **kwargs):
    print("[signal_analysis] ✅ 開始整合分析流程...")

    # 取得策略參數
    strategy = get_strategy_profile(mode)
    strategy.update(kwargs)  # 允許手動覆蓋參數

    min_turnover = strategy.get("min_turnover", 50_000_000)
    min_score = strategy.get("min_score", 5)
    price_limit = strategy.get("price_limit", 100)
    eps_limit = strategy.get("eps_limit", 100)
    include_weak = strategy.get("include_weak", True)

    # Step 1：擷取價格與成交金額資料
    print("[signal_analysis] ⏳ 擷取熱門股清單...")
    price_df = fetch_price_data(min_turnover=min_turnover, limit=price_limit)
    if price_df.empty:
        print("[signal_analysis] ⚠️ 熱門股清單為空，終止分析")
        return pd.DataFrame()

    stock_ids = price_df["stock_id"].tolist()
    print(f"[signal_analysis] 🔍 共擷取到 {len(stock_ids)} 檔熱門股")

    # Step 2：產生技術指標欄位
    print("[signal_analysis] 🔧 計算技術指標欄位...")
    price_df = generate_ta_signals(price_df)

    # Step 3：擷取 EPS 與殖利率資料
    print(f"[signal_analysis] ⏳ 擷取 EPS 與殖利率資料（最多 {eps_limit} 檔）...")
    eps_df = fetch_eps_dividend_data(stock_ids, limit=eps_limit)

    # Step 4：擷取法人籌碼資料
    print("[signal_analysis] ⏳ 擷取法人買賣超資料...")
    fund_df = fetch_fundamental_data()

    # Step 5：合併所有資料
    print("[signal_analysis] 🔧 合併所有來源資料...")
    df = price_df.merge(eps_df, on='stock_id', how='left') \
                 .merge(fund_df, on='stock_id', how='left')

    # Step 6：預處理欄位
    df["eps_growth"] = df["eps_growth"].fillna(False)
    df["dividend_yield"] = df["dividend_yield"].fillna(0.0)
    df["ytd_return"] = df["ytd_return"].fillna(0.0)
    df["buy_total"] = df["buy_total"].fillna(0)

    # Step 7：計算分數與建議
    print("[signal_analysis] 📊 計算技術分數與投資建議...")
    final_df = calculate_technical_scores(df)

    # Step 8：推薦與觀察股分流
    recommended = final_df[final_df['score'] >= min_score] \
                    .sort_values(by='score', ascending=False).reset_index(drop=True)

    if not recommended.empty:
        print(f"[signal_analysis] ✅ 推薦股票完成，共 {len(recommended)} 檔符合條件")
        return recommended

    # 無推薦股時，回傳觀察用前幾名
    if include_weak:
        fallback = final_df.sort_values(by='score', ascending=False).head(5).reset_index(drop=True)
        print("[signal_analysis] ⚠️ 無推薦股票，顯示前 5 檔觀察股供參考")
        return fallback
    else:
        return pd.DataFrame()
