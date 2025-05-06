# modules/strategy_profiles.py

print("[strategy_profiles] ✅ 已載入策略設定檔")

# 每個時段對應的策略設定
STRATEGY_PROFILES = {
    "opening": {
        "scan_limit": 100,
        "min_score": 4,
        "include_weak": True,
        "indicators": {
            "macd": 2.0,
            "kd": 1.5,
            "rsi": 1.0,
            "ma5": 1.0,
            "ma20": 1.0,
            "ma60": 0.5,
            "bollinger": 0.5,
        },
        "comment": "開盤推薦策略：適合短線快速進場評估。",
    },
    "intraday": {
        "scan_limit": 150,
        "min_score": 4,
        "include_weak": True,
        "indicators": {
            "macd": 2.0,
            "kd": 2.0,
            "rsi": 1.0,
            "ma5": 1.0,
            "ma20": 1.0,
        },
        "comment": "盤中追蹤策略：追蹤中小型波段股的盤中發動機會。",
    },
    "dividend": {
        "scan_limit": 200,
        "min_score": 4,
        "include_weak": True,
        "indicators": {
            "macd": 1.5,
            "kd": 1.5,
            "rsi": 1.0,
            "ma5": 0.5,
            "ma20": 0.5,
            "eps": 2.0,
            "dividend": 2.0
        },
        "comment": "中午策略：聚焦殖利率與短線反彈潛力。",
    },
    "closing": {
        "scan_limit": 450,
        "min_score": 5,
        "include_weak": True,
        "indicators": {
            "macd": 2.0,
            "kd": 1.5,
            "rsi": 1.0,
            "ma20": 1.0,
            "ma60": 1.0,
            "bollinger": 1.0,
            "eps": 2.0,
            "institutional": 2.0
        },
        "comment": "收盤策略：整日總結、法人動向與中長線潛力。",
    },
}
