# ✅ 調整後的 strategy_profiles.py（放寬推薦門檻 + 提升技術權重）
def get_strategy_profile(mode="opening"):
    """
    根據不同分析時段，回傳各技術/基本面指標的評分權重與掃描數量。
    """

    base_profile = {
        # 技術指標評分權重（總分 ≈ 7.5）
        "macd": 1.0,
        "kdj": 1.0,
        "rsi": 1.0,
        "ma": 1.5,         # ✅ 提升均線權重
        "bollinger": 1.0,   # ✅ 提升布林通道權重

        # 基本面與法人加分
        "buy_total": 1.0,
        "eps_growth": 1.0,
        "dividend_yield": 1.0,

        # 額外參數
        "include_weak": True,
        "fallback_top_n": 7,

        # 新增參數區
        "dividend_weight_conditional": True,
        "suppress_low_volume": True,
        "promote_large_cap": True,
        "apply_sentiment_adjustment": True,
        "limit_score": 8.0
    }

    if mode == "opening":
        base_profile.update({
            "min_score": 4.0,         # ✅ 降低推薦門檻
            "recommend_min": 5.0,     # ✅ 放寬觀察轉推薦的分數
            "recommend_max": 8,
            "price_limit": 100,
            "eps_limit": 100
        })

    elif mode == "intraday":
        base_profile.update({
            "min_score": 5.5,
            "recommend_min": 6.0,
            "recommend_max": 8,
            "price_limit": 150,
            "eps_limit": 150
        })

    elif mode == "dividend":
        base_profile.update({
            "min_score": 5.5,
            "recommend_min": 6.0,
            "recommend_max": 8,
            "price_limit": 200,
            "eps_limit": 200
        })

    elif mode == "closing":
        base_profile.update({
            "min_score": 6.0,
            "recommend_min": 6.5,
            "recommend_max": 8,
            "price_limit": 500,
            "eps_limit": 300
        })

    return base_profile
