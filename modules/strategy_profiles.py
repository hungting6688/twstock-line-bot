print("[strategy_profiles] ✅ 已載入最新版（含市場情緒權重）")

def get_strategy_profile(mode="opening"):
    strategies = {
        "opening": {
            "limit": 100,
            "min_score": 7,
            "include_weak": True,
            "weights": {
                "MACD": 2,
                "KD": 1.5,
                "RSI": 1,
                "MA": 1,
                "BB": 1,
                "dividend": 1,
                "eps": 2,
                "pe": 1,
                "roe": 1,
            },
        },
        "intraday": {
            "limit": 100,
            "min_score": 6,
            "include_weak": False,
            "weights": {
                "MACD": 1.5,
                "KD": 2,
                "RSI": 1.5,
                "MA": 1,
                "BB": 1,
                "dividend": 0.5,
                "eps": 1,
                "pe": 0.5,
                "roe": 0.5,
            },
        },
        "dividend": {
            "limit": 100,
            "min_score": 6,
            "include_weak": True,
            "weights": {
                "MACD": 1,
                "KD": 1,
                "RSI": 1,
                "MA": 1,
                "BB": 1,
                "dividend": 2,
                "eps": 1.5,
                "pe": 1,
                "roe": 1,
            },
        },
        "closing": {
            "limit": 300,
            "min_score": 6,
            "include_weak": True,
            "weights": {
                "MACD": 2,
                "KD": 1,
                "RSI": 1,
                "MA": 1,
                "BB": 1,
                "dividend": 1,
                "eps": 2,
                "pe": 1,
                "roe": 1.5,
            },
        }
    }

    return strategies.get(mode, strategies["opening"])
