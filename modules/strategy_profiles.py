def get_strategy_profile(mode="opening"):
    base_profile = {
        "macd": 2.0,
        "kdj": 2.0,
        "rsi": 1.5,
        "ma": 2.0,
        "bollinger": 1.5,
        "buy_total": 0.5,
        "eps_growth": 0.5,
        "dividend_yield": 0.5,
        "min_score": 5,
        "price_limit": 100,
        "eps_limit": 100,
        "fallback_top_n": 6,
        "include_weak": True
    }

    if mode == "opening":
        base_profile.update({
            "min_score": 5.0,
            "price_limit": 100,
            "eps_limit": 100,
            "fallback_top_n": 8
        })
    elif mode == "intraday":
        base_profile.update({
            "min_score": 5.5,
            "price_limit": 150,
            "eps_limit": 150,
            "fallback_top_n": 8
        })
    elif mode == "dividend":
        base_profile.update({
            "min_score": 5.5,
            "price_limit": 200,
            "eps_limit": 200,
            "fallback_top_n": 8
        })
    elif mode == "closing":
        base_profile.update({
            "min_score": 6.0,
            "price_limit": 500,
            "eps_limit": 300,
            "fallback_top_n": 8
        })

    return base_profile
