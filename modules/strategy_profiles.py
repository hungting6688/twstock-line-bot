def get_strategy_profile(mode="opening"):
    base_profile = {
        "macd": 1.0,
        "kdj": 1.0,
        "rsi": 1.0,
        "ma": 1.5,
        "bollinger": 1.0,
        "buy_total": 1.0,
        "eps_growth": 1.0,
        "dividend_yield": 1.0,
        "include_weak": True,
        "fallback_top_n": 7,
        "dividend_weight_conditional": True,
        "suppress_low_volume": True,
        "promote_large_cap": True,
        "apply_sentiment_adjustment": True,
        "limit_score": 8.0
    }

    if mode == "opening":
        base_profile.update({
            "min_score": 4.0,
            "recommend_min": 5.0,
            "recommend_max": 8,
            "price_limit": 100,
            "eps_limit": 100
        })
    elif mode == "intraday":
        base_profile.update({
            "min_score": 4.5,
            "recommend_min": 5.5,
            "recommend_max": 8,
            "price_limit": 150,
            "eps_limit": 150
        })
    elif mode == "dividend":
        base_profile.update({
            "min_score": 4.5,
            "recommend_min": 5.5,
            "recommend_max": 8,
            "price_limit": 200,
            "eps_limit": 200
        })
    elif mode == "closing":
        base_profile.update({
            "min_score": 5.0,
            "recommend_min": 6.0,
            "recommend_max": 8,
            "price_limit": 500,
            "eps_limit": 300
        })

    return base_profile
