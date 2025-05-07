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
        "include_weak": True
    }

    if mode == "opening":
        base_profile.update({ "min_score": 5, "price_limit": 100, "eps_limit": 100 })
    elif mode == "intraday":
        base_profile.update({ "min_score": 4.5, "price_limit": 150, "eps_limit": 150 })
    elif mode == "dividend":
        base_profile.update({ "min_score": 4.5, "price_limit": 200, "eps_limit": 200 })
    elif mode == "closing":
        base_profile.update({ "min_score": 4.0, "price_limit": 300, "eps_limit": 300 })

    return base_profile
