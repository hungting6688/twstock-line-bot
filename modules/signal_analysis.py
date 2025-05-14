print("[signal_analysis] ✅ 已載入最新版 (with get_top_stocks)")

import pandas as pd
from modules.price_fetcher import fetch_price_data
from modules.ta_generator import generate_ta_signals
from modules.eps_dividend_scraper import fetch_eps_dividend_data
from modules.fundamental_scraper import fetch_fundamental_data
from modules.strategy_profiles import get_strategy_profile

def analyze_stocks_with_signals(mode="opening"):
    strategy = get_strategy_profile(mode)
    limit = strategy.get("limit", 100)
    min_score = strategy.get("min_score", 7)
    include_weak = strategy.get("include_weak", False)
    weights = strategy.get("weights", {})

    print(f"[signal_analysis] ⏳ 擷取熱門股前 {limit} 檔...")
    price_df = fetch_price_data(limit=limit)

    if price_df.empty:
        raise ValueError("取得的股價資料無效")

    stock_ids = price_df["stock_id"].tolist()

    print("[signal_analysis] ⏳ 計算技術指標...")
    ta_df = generate_ta_signals(stock_ids)

    print("[signal_analysis] ⏳ 擷取 EPS / 殖利率 / YTD 報酬率...")
    eps_df = fetch_eps_dividend_data(stock_ids)

    print("[signal_analysis] ⏳ 擷取法人 / PE / ROE...")
    fund_df = fetch_fundamental_data(stock_ids)

    # 合併所有資料
    df = price_df.merge(ta_df, on="stock_id", how="left")
    df = df.merge(eps_df, on="stock_id", how="left")
    df = df.merge(fund_df, on="stock_id", how="left")

    results = []

    for _, row in df.iterrows():
        score = 0
        reasons = []

        def add_score(key, condition=True, label=None):
            w = weights.get(key, 0)
            if pd.notna(row.get(key)) and condition:
                nonlocal score
                score += w
                if label:
                    reasons.append(label)

        add_score("MACD", row.get("MACD") == 1, "MACD黃金交叉")
        add_score("KD", row.get("K", 0) > row.get("D", 100), "KD黃金交叉")
        add_score("RSI", row.get("RSI", 0) > 50, "RSI走強")
        add_score("MA", row.get("均線") == 1, "站上均線")
        add_score("BB", row.get("布林通道") == 1, "布林通道偏多")
        add_score("dividend", row.get("殖利率", 0) > 5, "高殖利率")
        add_score("eps", row.get("EPS", 0) > 2, "EPS優異")
        add_score("pe", row.get("本益比", 99) < 15, "本益比合理")
        add_score("roe", row.get("ROE", 0) > 10, "ROE高")

        label = ""
        if score >= min_score:
            label = "✅ 推薦"
        elif include_weak and score <= 1:
            label = "⚠️ 走弱"
        else:
            label = "📌 觀察"

        results.append({
            "stock_id": row["stock_id"],
            "name": row["name"],
            "score": round(score, 1),
            "label": label,
            "reasons": "、".join(reasons),
        })

    return results