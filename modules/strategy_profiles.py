# modules/strategy_profiles.py

print("[strategy_profiles] ✅ 已載入策略設定檔（含權重）")

STRATEGY_CONFIGS = {
    "opening": {
        "limit": 100,
        "min_score": 3.5,
        "include_weak": False,
        "weights": {
            "ma": 0.5,
            "macd": 1.5,
            "kd": 1.0,
            "rsi": 1.0,
            "boll": 0.5,
            "eps": 1.5,
            "dividend": 1.5
        }
    },
    "intraday": {
        "limit": 100,
        "min_score": 3.0,
        "include_weak": True,
        "weights": {
            "ma": 0.5,
            "macd": 1.2,
            "kd": 1.2,
            "rsi": 1.0,
            "boll": 0.5,
            "eps": 1.0,
            "dividend": 1.0
        }
    },
    "dividend": {
        "limit": 150,
        "min_score": 2.8,
        "include_weak": True,
        "weights": {
            "ma": 0.5,
            "macd": 1.2,
            "kd": 1.0,
            "rsi": 0.8,
            "boll": 0.5,
            "eps": 1.0,
            "dividend": 2.0
        }
    },
    "closing": {
        "limit": 450,
        "min_score": 3.2,
        "include_weak": True,
        "weights": {
            "ma": 0.7,
            "macd": 1.5,
            "kd": 1.0,
            "rsi": 1.0,
            "boll": 0.5,
            "eps": 2.0,
            "dividend": 1.5
        }
    }
}

def get_strategy(mode: str):
    return STRATEGY_CONFIGS.get(mode, STRATEGY_CONFIGS["opening"])