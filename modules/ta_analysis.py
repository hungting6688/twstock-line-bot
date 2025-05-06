# modules/ta_analysis.py

def analyze_technical_indicators(stock_ids: list[str]) -> dict:
    results = {}

    for sid in stock_ids:
        try:
            results[sid] = {
                "score": 4,  # ✅ 固定為 4 分測試
                "suggestion": "MACD 上揚 + KD 黃金交叉",
                "is_weak": False
            }
        except Exception as e:
            print(f"[{sid}] 技術指標分析失敗：{e}")
            continue

    return results
