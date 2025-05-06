print("[strategy_profiles] ✅ 已載入策略設定檔（含權重）")

STRATEGY_PROFILES = {
    "opening": {
        "scan_limit": 100,
        "min_score": 3.5,
        "include_weak": True,
        "indicators": ["macd", "kd", "rsi", "ma"],
        "weights": {
            "macd": 1.5,
            "kd": 1.2,
            "rsi": 1.0,
            "ma": 1.0,
            "eps": 1.3,
            "dividend": 1.0
        },
        "comment": "開盤熱門股技術分析"
    },
    "intraday": {
        "scan_limit": 150,
        "min_score": 4.0,
        "include_weak": True,
        "indicators": ["macd", "kd", "rsi", "ma"],
        "weights": {
            "macd": 1.3,
            "kd": 1.3,
            "rsi": 1.1,
            "ma": 1.0,
            "eps": 1.0,
            "dividend": 1.0
        },
        "comment": "盤中中小型股監控"
    },
    "dividend": {
        "scan_limit": 200,
        "min_score": 4.2,
        "include_weak": True,
        "indicators": ["macd", "kd", "rsi", "ma", "eps"],
        "weights": {
            "macd": 1.0,
            "kd": 1.0,
            "rsi": 1.0,
            "ma": 1.0,
            "eps": 1.5,
            "dividend": 1.5
        },
        "comment": "午盤短線機會偵測"
    },
    "closing": {
        "scan_limit": 300,
        "min_score": 5.0,
        "include_weak": True,
        "indicators": ["macd", "kd", "rsi", "ma", "eps", "dividend"],
        "weights": {
            "macd": 1.3,
            "kd": 1.0,
            "rsi": 1.0,
            "ma": 1.0,
            "eps": 1.5,
            "dividend": 1.5
        },
        "comment": "收盤中長線潛力股分析"
    }
}
