print("[signal_analysis] ✅ 已載入最新版 (with get_top_stocks)")

import pandas as pd
from modules.price_fetcher import get_top_stocks
from modules.ta_generator import generate_technical_indicators
from modules.strategy_profiles import get_strategy_profile
from modules.eps_dividend_scraper import fetch_eps_dividend_data
from modules.fundamental_scraper import fetch_fundamental_data

def analyze_stocks_with_signals(strategy="default", limit=100, min_score=5, include_weak=True, **kwargs):
    print(f"[signal_analysis] ✅ 開始整合分析流程（策略：{strategy}）...")

    try:
        # 熱門股代碼清單
        stock_ids = get_top_stocks(limit=limit)
        print(f"[signal_analysis] ⏳ 擷取熱門股清單（共 {len(stock_ids)} 檔）")

        # 擷取資料
        price_df = generate_technical_indicators(stock_ids)
        eps_df = fetch_eps_dividend_data(stock_ids)
        fund_df = fetch_fundamental_data(stock_ids)

        # 整合所有資料
        merged = price_df.merge(eps_df, on="stock_id", how="left")
        merged = merged.merge(fund_df, on="stock_id", how="left")
        merged = merged.dropna(subset=["score"], how="all")

        # 套用策略設定
        strategy_profile = get_strategy_profile(strategy)
        score_col = "score"
        merged[score_col] = 0

        # 根據技術指標加權評分
        for col, weight in strategy_profile["weights"].items():
            merged[score_col] += merged.get(col, 0) * weight

        # 生成建議與標籤
        def get_label(row):
            if row[score_col] >= min_score:
                return "✅ 推薦"
            elif include_weak and row[score_col] <= -3:
                return "⚠️ 走弱"
            else:
                return "📌 觀察"

        def get_comment(score):
            if score >= 8:
                return "建議立即列入關注清單"
            elif score >= 6:
                return "建議密切觀察進出點"
            elif score >= 3:
                return "建議觀察，不宜追高"
            elif score >= 0:
                return "建議暫不進場"
            else:
                return "不建議操作"

        merged["label"] = merged.apply(get_label, axis=1)
        merged["comment"] = merged[score_col].apply(get_comment)

        # 推薦與觀察股
        recommended = merged[merged["label"] == "✅ 推薦"]
        if recommended.empty:
            fallback = merged.sort_values(by=score_col, ascending=False).head(8)
            print("[signal_analysis] ⚠️ 無推薦股，顯示觀察股 top N")
            return fallback
        else:
            top = recommended.sort_values(by=score_col, ascending=False).head(8)
            return top

    except Exception as e:
        print(f"[signal_analysis] ❌ 分析過程錯誤：{e}")
        return pd.DataFrame()
