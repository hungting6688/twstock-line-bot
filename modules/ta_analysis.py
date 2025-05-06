# modules/ta_analysis.py

def analyze_technical_indicators(stock_ids: list[str]) -> dict:
    """
    根據輸入的股票代碼清單，回傳每檔股票的技術指標分析結果（測試用範例）。
    
    回傳格式應包含：
        - score: 推薦分數
        - suggestion: 白話建議文字
        - is_weak: 是否為極弱股（True/False）
    """
    results = {}

    for sid in stock_ids:
        try:
            # 模擬固定分數與訊號文字（用於測試架構是否跑通）
            results[sid] = {
                "score": 4,  # 模擬總分（例如符合 MACD、KD、均線等指標）
                "suggestion": "MACD 上揚 + KD 黃金交叉",  # 模擬白話建議
                "is_weak": False  # 模擬極弱判斷（RSI < 30 且跌破均線）
            }
        except Exception as e:
            print(f"[{sid}] 技術指標分析失敗：{e}")
            continue

    return results
