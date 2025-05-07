import pandas as pd

def calculate_technical_scores(df, strategy=None):
    print("[ta_analysis] ✅ 開始評分")

    # 使用預設權重，若未提供 strategy
    weights = strategy.get("weights", {}) if strategy else {
        "macd": 2,
        "kdj": 2,
        "rsi": 1.5,
        "ma": 2,
        "bollinger": 1.5,
        "buy_total": 0.5,
        "eps_growth": 0.5,
        "dividend": 0.5,
    }

    result = []

    for _, row in df.iterrows():
        score = 0.0
        reasons = []
        suggestion = ""

        # 技術指標評分邏輯
        if row.get("macd_signal", False):
            score += weights.get("macd", 0)
            reasons.append("MACD黃金交叉")

        if row.get("kdj_signal", False):
            score += weights.get("kdj", 0)
            reasons.append("KD黃金交叉")

        if row.get("rsi_signal", False):
            score += weights.get("rsi", 0)
            reasons.append("RSI走強")

        if row.get("ma_signal", False):
            score += weights.get("ma", 0)
            reasons.append("站上均線")

        if row.get("bollinger_signal", False):
            score += weights.get("bollinger", 0)
            reasons.append("布林通道偏多")

        # 基本面條件
        if row.get("buy_total", 0) > 0:
            score += weights.get("buy_total", 0)
            reasons.append("法人買超")

        if row.get("eps_growth", False):
            score += weights.get("eps_growth", 0)
            reasons.append("EPS成長")

        if row.get("dividend_yield", 0) >= 3 and row.get("ytd_return", 0) > 0:
            score += weights.get("dividend", 0)
            reasons.append("高殖利率")

        # 白話建議
        if score >= 7:
            suggestion = "建議立即列入關注清單"
        elif score >= 5:
            suggestion = "建議密切觀察"
        elif score >= 3:
            suggestion = "建議暫不進場"
        else:
            suggestion = "不建議操作"

        result.append({
            "stock_id": row["stock_id"],
            "stock_name": row.get("stock_name", ""),
            "score": round(score, 2),
            "reasons": "、".join(reasons),
            "suggestion": suggestion
        })

    return pd.DataFrame(result)
