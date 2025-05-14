# modules/signal_analysis.py
print("[signal_analysis] ✅ 已載入最新版 (with get_top_stocks)")

import pandas as pd
from modules.price_fetcher import fetch_price_data
from modules.ta_generator import generate_ta_signals
from modules.eps_dividend_scraper import fetch_eps_dividend_data
from modules.fundamental_scraper import fetch_fundamental_data
from modules.strategy_profiles import get_strategy_profile


def analyze_stocks_with_signals(mode="default", limit=100, min_score=6, include_weak=True, **kwargs):
    print(f"[signal_analysis] ✅ 開始整合分析流程（策略：{mode}）...")

    # 抓取熱門股
    price_df = fetch_price_data(limit=limit)
    stock_ids = price_df["證券代號"].tolist()

    # 加入技術指標欄位
    price_df = generate_ta_signals(price_df)

    # 加入 EPS / 殖利率 / YTD
    eps_df = fetch_eps_dividend_data(stock_ids[:20])  # 避免封鎖，限制20檔
    merged = pd.merge(price_df, eps_df, on="證券代號", how="left")

    # 加入法人 / 本益比等基本面
    try:
        fundamental_df = fetch_fundamental_data(stock_ids)
        merged = pd.merge(merged, fundamental_df, on="證券代號", how="left")
    except Exception as e:
        print(f"[signal_analysis] ❌ 分析過程錯誤：{e}")
        return []

    # 載入該模式對應策略
    strategy = get_strategy_profile(mode)

    def score(row):
        s = 0
        for key, weight in strategy["weights"].items():
            if key in row and pd.notna(row[key]):
                if isinstance(row[key], (int, float, bool)):
                    s += row[key] * weight
        return round(s, 2)

    merged["推薦分數"] = merged.apply(score, axis=1)
    merged = merged.sort_values("推薦分數", ascending=False)

    # 標記分類
    def classify(row):
        if row["推薦分數"] >= min_score:
            return "✅ 推薦"
        elif include_weak and row.get("rsi_strong") == 0 and row.get("kd_golden") == 0:
            return "⚠️ 走弱"
        else:
            return "📌 觀察"

    merged["分類"] = merged.apply(classify, axis=1)

    return merged
