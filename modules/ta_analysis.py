import pandas as pd

def analyze_signals(df: pd.DataFrame) -> dict:
    score = 0
    reasons = []
    suggestions = []

    # MACD
    if df["MACD_diff"] > 0 and df["MACD"] > 0:
        score += 1.2
        reasons.append("🟢 MACD多頭排列")
        suggestions.append("MACD 呈現正向，趨勢偏多，考慮觀察是否有突破訊號")

    elif df["MACD_diff"] < 0 and df["MACD"] < 0:
        score -= 1.2
        reasons.append("🔻 MACD空頭排列")
        suggestions.append("MACD 處於弱勢區，避免進場，或評估是否反彈")

    # RSI
    if df["RSI6"] < 30:
        score += 1
        reasons.append("🟢 RSI < 30 超跌區")
        suggestions.append("RSI 過低，短線可能反彈，可觀察量價變化")

    elif df["RSI6"] > 70:
        score -= 1
        reasons.append("🔻 RSI > 70 過熱")
        suggestions.append("RSI 偏高，須提防漲多拉回")

    # KD 黃金交叉
    if df["K"] > df["D"]:
        score += 1
        reasons.append("🟢 KD 黃金交叉")
        suggestions.append("KD 呈現黃金交叉，技術轉強，可考慮留意進場點")

    # 均線
    if df["MA5"] > df["MA20"]:
        score += 1
        reasons.append("🟢 均線多頭排列")
        suggestions.append("短均線突破長均線，顯示短線趨勢轉強")

    elif df["MA5"] < df["MA20"]:
        score -= 1
        reasons.append("🔻 均線空頭排列")
        suggestions.append("短均線在長均線下方，顯示趨勢仍偏弱")

    # 布林通道下緣反彈
    if df["Close"] < df["BOLL_LB"]:
        score += 0.5
        reasons.append("🟢 跌破布林下緣")
        suggestions.append("股價偏離布林下軌，可能反彈，可觀察止穩情況")

    # 終極弱勢判斷
    if score <= -2.5:
        reasons.append("⚠️ 技術面極弱")
        suggestions.append("此股技術面訊號全面偏空，暫不建議介入")

    return {
        "score": round(score, 2),
        "reasons": reasons,
        "suggestions": suggestions
    }
