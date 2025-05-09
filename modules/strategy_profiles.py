def get_strategy_profile(mode="opening"):
    """
    根據不同分析時段，回傳各技術/基本面指標的評分權重與掃描數量。
    """

    base_profile = {
        # 技術指標評分權重（總分 ≈ 6.5）
        "macd": 1.0,
        "kdj": 0.5,
        "rsi": 0.5,
        "ma": 1.0,
        "bollinger": 0.5,

        # 基本面與法人加分
        "buy_total": 1.0,
        "eps_growth": 1.0,
        "dividend_yield": 1.0,  # 若啟用條件式則需搭配 eps/buy_total 才給滿分

        # 額外參數
        "include_weak": True,
        "fallback_top_n": 7,  # 無推薦時顯示觀察股數量

        # 新增參數區
        "dividend_weight_conditional": True,  # 殖利率需符合條件才能加滿分
        "suppress_low_volume": True,          # 冷門股降分（低成交量 or 小市值）
        "promote_large_cap": True,            # 大型股適度加分
        "apply_sentiment_adjustment": True,   # 套用市場氣氛修正
        "limit_score": 7.0                    # 總分上限
    }

    if mode == "opening":
        base_profile.update({
            "min_score": 5.0,
            "recommend_min": 6.0,
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
