# modules/strategy_profiles.py

def get_strategy_profile(mode="opening"):
    """
    根據不同分析時段，回傳各技術/基本面指標的評分權重與掃描數量。
    """

    base_profile = {
        "macd": 1.5,
        "kdj": 1.5,
        "rsi": 1.0,
        "ma": 1.5,
        "bollinger": 1.0,
        "buy_total": 0.5,
        "eps_growth": 1.0,
        "dividend_yield": 0.5,
        "min_score": 6.0,
        "price_limit": 100,
        "eps_limit": 100,
        "include_weak": True
    }

    if mode == "opening":
        base_profile.update({
            "min_score": 6.0,
            "price_limit": 100,
            "eps_limit": 100,
            "buy_total": 0.5,
            "dividend_yield": 0.5
        })

    elif mode == "intraday":
        base_profile.update({
            "macd": 1.5,
            "kdj": 1.5,
            "rsi": 1.0,
            "ma": 1.0,
            "bollinger": 1.0,
            "buy_total": 0.2,
            "eps_growth": 0.0,
            "dividend_yield": 0.0,
            "min_score": 5.5,
            "price_limit": 150,
            "eps_limit": 0
        })

    elif mode == "dividend":
        base_profile.update({
            "macd": 1.0,
            "kdj": 1.0,
            "rsi": 1.0,
            "ma": 1.0,
            "bollinger": 1.0,
            "buy_total": 0.5,
            "eps_growth": 1.0,
            "dividend_yield": 1.0,
            "min_score": 5.5,
            "price_limit": 200,
            "eps_limit": 200
        })

    elif mode == "closing":
        base_profile.update({
            "macd": 1.0,
            "kdj": 1.0,
            "rsi": 1.0,
            "ma": 1.0,
            "bollinger": 1.0,
            "buy_total": 1.0,
            "eps_growth": 1.0,
            "dividend_yield": 1.0,
            "min_score": 6.0,
            "price_limit": 500,
            "eps_limit": 300
        })

    return base_profile
