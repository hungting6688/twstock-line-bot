# ✅ strategy_profiles.py（新增 weak_threshold）
def get_strategy_profile(mode="opening"):
    """
    根據不同分析時段，回傳各技術/基本面指標的評分權重與掃描數量。
    """
    base_profile = {
        # 技術指標評分權重
        "macd": 1.0,
        "kdj": 0.5,
        "rsi": 0.5,
        "ma": 1.0,
        "bollinger": 0.5,

        # 基本面加分
        "buy_total": 1.0,
        "eps_growth": 1.0,
        "dividend_yield": 1.0,

        # 額外參數
        "include_weak": True,
        "fallback_top_n": 7,
        "dividend_weight_conditional": True,
        "suppress_low_volume": True,
        "promote_large_cap": True,
        "apply_sentiment_adjustment": True,
        "limit_score": 7.0,
        "weak_threshold": 2  # 判定走弱的技術指標數
    }

    if mode == "opening":
        base_profile.update({
            "min_score": 5.0,
            "recommend_min": 6.0,
            "recommend_max": 8,
            "price_limit": 100,
            "eps_limit": 100,
            "rsi_period": 9,
            "ma_periods": [5, 10],
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9
        })

    elif mode == "intraday":
        base_profile.update({
            "min_score": 5.5,
            "recommend_min": 6.0,
            "recommend_max": 8,
            "price_limit": 150,
            "eps_limit": 150,
            "rsi_period": 6,
            "ma_periods": [5],
            "macd_fast": 9,
            "macd_slow": 21,
            "macd_signal": 6
        })

    elif mode == "dividend":
        base_profile.update({
            "min_score": 5.5,
            "recommend_min": 6.0,
            "recommend_max": 8,
            "price_limit": 200,
            "eps_limit": 200,
            "rsi_period": 9,
            "ma_periods": [10, 20],
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9
        })

    elif mode == "closing":
        base_profile.update({
            "min_score": 6.0,
            "recommend_min": 6.5,
            "recommend_max": 8,
            "price_limit": 500,
            "eps_limit": 300,
            "rsi_period": 14,
            "ma_periods": [20, 60],
            "macd_fast": 8,
            "macd_slow": 21,
            "macd_signal": 5
        })

    return base_profile
