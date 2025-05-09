def get_strategy_profile(mode="opening"):
    """
    根據不同分析時段，回傳各技術/基本面指標的評分權重與掃描數量。
    """

    base_profile = {
        # 技術指標評分權重
        "macd": 2.0,
        "kdj": 2.0,
        "rsi": 1.5,
        "ma": 2.0,
        "bollinger": 1.5,

        # 基本面與法人加分
        "buy_total": 0.5,
        "eps_growth": 0.5,
        "dividend_yield": 0.5,

        # 推薦股數與弱勢提醒
        "recommend_min": 6,
        "recommend_max": 8,
        "include_weak": True
    }

    if mode == "opening":
        base_profile.update({
            "min_score": 5.0,
            "price_limit": 100,
            "eps_limit": 100,
        })

    elif mode == "intraday":
        base_profile.update({
            "min_score": 5.5,
            "price_limit": 200,
            "eps_limit": 150,
        })

    elif mode == "dividend":
        base_profile.update({
            "min_score": 5.5,
            "price_limit": 300,
            "eps_limit": 200,
        })

    elif mode == "closing":
        base_profile.update({
            "min_score": 6.0,
            "price_limit": 500,
            "eps_limit": 300,
        })

    return base_profile
