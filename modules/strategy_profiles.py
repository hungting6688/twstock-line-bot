# modules/strategy_profiles.py
print("[strategy_profiles] ✅ 已載入最新版（含市場情緒權重）")

strategy_profiles = {
    "default": {
        "limit": 100,
        "min_score": 6,
        "include_weak": False,
        "filter_type": None,
        "weights": {
            "macd_golden": 2,
            "kd_golden": 2,
            "rsi_strong": 1,
            "above_ma": 1,
            "bollinger_strong": 1,
            "high_dividend": 1,
            "positive_eps": 1,
            "roe_rank": 1,
            "pe_rank": 1,
            "ytd_rank": 1,
            "buy_pressure": 1,
        },
        "sentiment_boost_weight": 0.3,  # 動態加權因子（例：0.3 代表情緒指數乘以 0.3 分）
        "max_recommend": 8
    },
    "intraday": {
        "limit": 100,
        "min_score": 5,
        "include_weak": True,
        "filter_type": "small_cap",
        "weights": {
            "macd_golden": 2,
            "kd_golden": 2,
            "rsi_strong": 1,
            "above_ma": 1,
            "bollinger_strong": 1,
            "high_dividend": 0,
            "positive_eps": 1,
            "roe_rank": 1,
            "pe_rank": 0,
            "ytd_rank": 1,
            "buy_pressure": 1,
        },
        "sentiment_boost_weight": 0.2,
        "max_recommend": 8
    },
    "dividend": {
        "limit": 100,
        "min_score": 6,
        "include_weak": True,
        "filter_type": "small_cap",
        "weights": {
            "macd_golden": 1,
            "kd_golden": 2,
            "rsi_strong": 1,
            "above_ma": 0,
            "bollinger_strong": 1,
            "high_dividend": 2,
            "positive_eps": 1,
            "roe_rank": 1,
            "pe_rank": 0,
            "ytd_rank": 0,
            "buy_pressure": 1,
        },
        "sentiment_boost_weight": 0.25,
        "max_recommend": 8
    },
    "closing": {
        "limit": 300,
        "min_score": 5,
        "include_weak": True,
        "filter_type": None,
        "weights": {
            "macd_golden": 2,
            "kd_golden": 2,
            "rsi_strong": 1,
            "above_ma": 1,
            "bollinger_strong": 1,
            "high_dividend": 1,
            "positive_eps": 1,
            "roe_rank": 1,
            "pe_rank": 1,
            "ytd_rank": 1,
            "buy_pressure": 2,
        },
        "sentiment_boost_weight": 0.3,
        "max_recommend": 8
    },
}
