def get_strategy_profile(mode="opening"):
    """
    根據不同分析時段，回傳各技術/基本面指標的評分權重與掃描數量。
    """

    base_profile = {
        # 技術指標評分權重（調整為較具辨識力的總分）
        "macd": 1.5,
        "kdj": 1.0,
        "rsi": 1.0,
        "ma": 1.0,
        "bollinger": 1.0,

        # 基本面與法人加分（合計約 3.0）
        "buy_total": 1.0,
        "eps_growth": 1.0,
        "dividend_yield": 1.0,

        # 額外條件邏輯
        "dividend_weight_conditional": True,  # 殖利率需搭配 EPS 或法人才加分
        "suppress_low_volume": True,          # 冷門股降分（低成交量、小市值）
        "promote_large_cap": True,            # 大型股加分（成交量高+市值高）
        "apply_sentiment_adjustment": True,   # 套用市場氣氛修正
        "limit_score": 7.0,                   # 總分上限控制
        "include_weak": True,                 # 顯示走弱股提示
        "fallback_top_n": 7                   # 無推薦時 fallback 觀察股數量
    }

    if mode == "opening":
        base_profile.update({
            "min_score": 4.0,           # ✅ 技術為主容忍度較高
            "recommend_min": 6.0,
            "recommend_max": 8,
            "price_limit": 100,
            "eps_limit": 100
        })

    elif mode == "intraday":
        base_profile.update({
            "min_score": 5.0,           # ✅ 聚焦中小型短期機會
            "recommend_min": 6.0,
            "recommend_max": 8,
            "price_limit": 150,
            "eps_limit": 150
        })

    elif mode == "dividend":
        base_profile.update({
            "min_score": 5.0,           # ✅ 著重殖利率與籌碼條件
            "recommend_min": 6.0,
            "recommend_max": 8,
            "price_limit": 200,
            "eps_limit": 200
        })

    elif mode == "closing":
        base_profile.update({
            "min_score": 5.5,           # ✅ 收盤偏重中長期強勢股
            "recommend_min": 6.5,
            "recommend_max": 8,
            "price_limit": 500,
            "eps_limit": 300
        })

    return base_profile
