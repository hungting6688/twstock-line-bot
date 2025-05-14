print("[ta_analysis] ✅ 已載入最新版（含權重評分與建議）")

import pandas as pd
from modules.ta_generator import generate_technical_indicators
from modules.market_sentiment import get_market_sentiment_score

# 基礎建議邏輯（以分數為核心）
def get_suggestion(score):
    if score >= 8:
        return "建議立即列入關注清單"
    elif score >= 6:
        return "建議密切觀察，可短期介入"
    elif score >= 4:
        return "建議觀望，等待訊號明確"
    else:
        return "不建議操作，動能偏弱"

def analyze_technical_indicators(stock_ids):
    print("[ta_analysis] ⏳ 執行技術指標分析...")
    df = generate_technical_indicators(stock_ids)
    results = {}

    # 動態調整權重：根據市場情緒
    sentiment_score = get_market_sentiment_score()  # 0~10
    print(f"[ta_analysis] 📊 市場情緒分數：{sentiment_score}/10")

    # 基礎權重配置
    base_weights = {
        "MACD": 2.0,
        "KD": 2.0,
        "RSI": 2.0,
        "均線": 2.0,
        "布林通道": 2.0
    }

    # 根據情緒分數調整（舉例：情緒越高 MACD、均線加重，KD/RSI 減輕）
    adjust_factor = (sentiment_score - 5) / 5  # -1 ~ +1
    weights = {
        "MACD": base_weights["MACD"] * (1 + 0.3 * adjust_factor),
        "KD": base_weights["KD"] * (1 - 0.2 * adjust_factor),
        "RSI": base_weights["RSI"] * (1 - 0.2 * adjust_factor),
        "均線": base_weights["均線"] * (1 + 0.3 * adjust_factor),
        "布林通道": base_weights["布林通道"] * (1 + 0.1 * adjust_factor),
    }
    print(f"[ta_analysis] ✅ 權重配置：{weights}")

    for _, row in df.iterrows():
        sid = row["證券代號"]
        score = 0
        detail = []

        if row.get("MACD") == 1:
            score += weights["MACD"]
            detail.append("MACD 黃金交叉")
        if row.get("K", 50) > row.get("D", 50):
            score += weights["KD"]
            detail.append("KD 黃金交叉")
        if row.get("RSI", 50) > 50:
            score += weights["RSI"]
            detail.append("RSI 強勢")
        if row.get("均線") == 1:
            score += weights["均線"]
            detail.append("站上均線")
        if row.get("布林通道") == 1:
            score += weights["布林通道"]
            detail.append("布林通道偏多")

        is_weak = (row.get("RSI", 50) < 30 and row.get("均線") == 0)

        results[sid] = {
            "score": round(score, 1),
            "reasons": ", ".join(detail),
            "suggestion": get_suggestion(score),
            "is_weak": is_weak
        }

    print(f"[ta_analysis] ✅ 技術指標分析完成，共 {len(results)} 檔")
    return results
