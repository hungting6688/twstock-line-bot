import pandas as pd
from modules.price_fetcher import fetch_price_data
from modules.eps_dividend_scraper import fetch_eps_and_dividend
from modules.fundamental_scraper import fetch_fundamental_data
from modules.ta_generator import generate_technical_signals
from modules.ta_analysis import score_technical_signals
from modules.market_sentiment import get_market_sentiment
from modules.strategy_profiles import get_strategy_profile


def analyze_stocks_with_signals(mode="opening"):
    print("[signal_analysis] ✅ 開始整合分析流程...")

    # 取得策略配置
    strategy = get_strategy_profile(mode)
    min_turnover = strategy.get("min_turnover", 5000)
    price_limit = strategy.get("price_limit", 100)

    print("[signal_analysis] ⏳ 擷取熱門股清單...")
    price_df = fetch_price_data(min_turnover=min_turnover, limit=price_limit, mode=mode, strategy=strategy)
    if price_df.empty:
        print("[signal_analysis] ⚠️ 熱門股清單為空，終止分析")
        return None
    print(f"[signal_analysis] 🔍 共擷取到 {len(price_df)} 檔股票")

    print(f"[signal_analysis] ⏳ 擷取 EPS 與殖利率資料（最多 {len(price_df)} 檔）...")
    eps_df = fetch_eps_and_dividend(price_df["stock_id"].tolist())

    print("[signal_analysis] ⏳ 擷取法人買賣超資料...")
    fundamental_df = fetch_fundamental_data()

    print("[signal_analysis] 🔧 合併所有來源資料...")
    df = price_df.merge(eps_df, on="stock_id", how="left")
    df = df.merge(fundamental_df, on="stock_id", how="left")

    print("[signal_analysis] ⚙️ 產生技術指標欄位...")
    df = generate_technical_signals(df)

    sentiment_info = get_market_sentiment() if strategy.get("apply_sentiment_adjustment", False) else None
    print(f"[signal_analysis] 📈 市場氣氛：{sentiment_info['note']} ➔ 分數乘以 {sentiment_info['factor']}" if sentiment_info else "")

    print("[signal_analysis] 📊 計算技術分數與投資建議...")
    df = score_technical_signals(df, strategy, sentiment_info)

    # 排除無分數資料
    scored_df = df[df["score"].notna()].copy()
    if scored_df.empty:
        print("[signal_analysis] ⚠️ 無分數評分結果")
        return None

    scored_df.sort_values(by="score", ascending=False, inplace=True)

    # 分類 label
    min_score = strategy.get("min_score", 5.0)
    recommend_min = strategy.get("recommend_min", 6.0)
    recommend_max = strategy.get("recommend_max", 8)
    fallback_top_n = strategy.get("fallback_top_n", 5)

    def assign_label(score):
        if score >= recommend_min:
            return "✅ 推薦股"
        elif score >= min_score:
            return "👀 觀察股"
        else:
            return "🚫 不建議"

    scored_df["label"] = scored_df["score"].apply(assign_label)

    # 補齊欄位空值
    scored_df["suggestion"] = scored_df["suggestion"].fillna("-")
    scored_df["reasons"] = scored_df["reasons"].fillna("-")

    # 擷出前 N 名推薦 + fallback
    final_df = scored_df[scored_df["label"] == "✅ 推薦股"].head(recommend_max)
    if final_df.empty:
        fallback_df = scored_df.head(fallback_top_n).copy()
        if strategy.get("include_weak", False):
            print("[signal_analysis] ⚠️ 無推薦股票，顯示觀察股供參考")
        return fallback_df.reset_index(drop=True)

    return final_df.reset_index(drop=True)
