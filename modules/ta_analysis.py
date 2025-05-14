print("[ta_analysis] ✅ 已載入最新版（含權重評分與建議）")

from modules.ta_generator import generate_ta_signals
from modules.market_sentiment import get_market_sentiment_adjustments

def analyze_technical_indicators(stock_ids):
    raw_df = generate_ta_signals(stock_ids)
    if raw_df.empty:
        return {}

    weights = get_market_sentiment_adjustments()
    results = {}

    for _, row in raw_df.iterrows():
        sid = row["證券代號"]
        score = 0
        desc = []

        # MACD
        if row["MACD"] == 1:
            score += 1 * weights.get("MACD", 1.0)
            desc.append("MACD黃金交叉")

        # KD
        if row["K"] < 80 and row["K"] > row["D"]:
            score += 1 * weights.get("KD", 1.0)
            desc.append("KD黃金交叉")

        # RSI
        if row["RSI"] > 50:
            score += 1 * weights.get("RSI", 1.0)
            desc.append("RSI走強")

        # 均線
        if row["均線"] == 1:
            score += 1 * weights.get("MA", 1.0)
            desc.append("站上均線")

        # 布林通道
        if row["布林通道"] == 1:
            score += 1 * weights.get("BB", 1.0)
            desc.append("布林通道偏多")

        label = "📌 觀察"
        suggestion = "建議密切觀察"
        if score >= 7:
            label = "✅ 推薦"
            suggestion = "建議立即列入關注清單"
        elif row["RSI"] < 30 and row["均線"] == 0:
            label = "⚠️ 走弱"
            suggestion = "不建議操作，短線偏空"

        results[sid] = {
            "score": round(score, 1),
            "desc": "、".join(desc),
            "label": label,
            "suggestion": suggestion,
            "is_weak": (label == "⚠️ 走弱")
        }

    return results
