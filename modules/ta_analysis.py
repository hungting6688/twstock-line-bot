print("[ta_analysis] ✅ 已載入最新版（含權重評分與建議）")

def analyze_technical_indicators(stock_ids):
    from modules.ta_generator import generate_ta_signals

    raw_df = generate_ta_signals(stock_ids)
    result = {}

    for _, row in raw_df.iterrows():
        sid = row["證券代號"]
        score = 0
        tags = []

        # MACD 黃金交叉
        if row.get("MACD") == 1:
            score += 2
            tags.append("MACD 黃金交叉")

        # KD 黃金交叉
        if row.get("K") is not None and row.get("D") is not None:
            k, d = row["K"], row["D"]
            if k > d and k < 80:
                score += 2
                tags.append("KD 黃金交叉")
            elif k < 20:
                tags.append("RSI/K 過低")

        # RSI 走強
        if row.get("RSI") is not None and row["RSI"] > 50:
            score += 1
            tags.append("RSI 走強")
        elif row.get("RSI") is not None and row["RSI"] < 30:
            tags.append("RSI 過低")

        # 均線站上
        if row.get("均線") == 1:
            score += 2
            tags.append("站上均線")

        # 布林通道偏多
        if row.get("布林通道") == 1:
            score += 1
            tags.append("布林通道偏多")

        # 白話建議
        if score >= 6:
            suggestion = "建議立即列入關注清單"
        elif score >= 4:
            suggestion = "建議密切觀察"
        elif score >= 2:
            suggestion = "建議暫不進場"
        else:
            suggestion = "不建議操作"

        # 是否為極弱股
        is_weak = ("RSI 過低" in tags or "RSI/K 過低" in tags) and row.get("均線") == 0

        result[sid] = {
            "score": score,
            "tags": tags,
            "suggestion": suggestion,
            "is_weak": is_weak
        }

    return result
