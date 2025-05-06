# modules/strategy_profiles.py
print("[strategy_profiles] ✅ 已載入策略設定檔")

STRATEGY_PROFILES = {
    "opening": {
        "scan_limit": 100,
        "min_score": 3.5,
        "include_weak": True,
        "indicators": ["macd", "kd", "rsi", "ma"],
        "comment": "開盤熱門股技術分析"
    },
    "intraday": {
        "scan_limit": 150,
        "min_score": 4.5,
        "include_weak": True,
        "indicators": ["macd", "kd", "rsi", "ma"],
        "comment": "盤中中小型股監控"
    },
    "dividend": {
        "scan_limit": 200,
        "min_score": 4.0,
        "include_weak": True,
        "indicators": ["macd", "kd", "rsi", "ma"],
        "comment": "午盤短線機會偵測"
    },
    "closing": {
        "scan_limit": 500,
        "min_score": 5.0,
        "include_weak": True,
        "indicators": ["macd", "kd", "rsi", "ma", "eps", "dividend"],
        "comment": "收盤中長線潛力股分析"
    }
}
