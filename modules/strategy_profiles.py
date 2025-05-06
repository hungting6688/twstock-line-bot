print("[strategy_profiles] ✅ 已載入策略設定檔（含權重）")

STRATEGY_PROFILES = {
    "opening": {
        "scan_limit": 100,
        "min_score": 3.5,
        "include_weak": True,
        "weights": {
            "macd": 1.2,
            "kd": 1.0,
            "rsi": 0.8,
            "ma": 1.0,
            "eps": 1.5,
            "dividend": 1.5
        }
    },
    "intraday": {
        "scan_limit": 100,
        "min_score": 3.0,
        "include_weak": True,
        "weights": {
            "macd": 1.2,
            "kd": 1.2,
            "rsi": 1.0,
            "ma": 1.0,
            "eps": 1.2
        }
    },
    "dividend": {
        "scan_limit": 120,
        "min_score": 3.5,
        "include_weak": False,
        "weights": {
            "macd": 1.0,
            "kd": 1.0,
            "rsi": 0.8,
            "ma": 1.0,
            "eps": 1.3,
            "dividend": 1.7
        }
    },
    "closing": {
        "scan_limit": 300,
        "min_score": 3.0,
        "include_weak": True,
        "weights": {
            "macd": 1.3,
            "kd": 1.2,
            "rsi": 1.0,
            "ma": 1.0,
            "eps": 1.5,
            "dividend": 1.5
        }
    }
}
