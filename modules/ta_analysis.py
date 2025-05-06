# modules/ta_analysis.py

def analyze_technical_indicators(stock_ids: list[str]) -> dict:
    print("[ta_analysis] 模擬固定分數回傳")
    return {
        sid: {
            "score": 4,
            "suggestion": "MACD 上揚 + KD 黃金交叉",
            "is_weak": False
        }
        for sid in stock_ids
    }
