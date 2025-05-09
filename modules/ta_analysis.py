import pandas as pd

def calculate_technical_scores(df, **config):
    print("[ta_analysis] ✅ 開始評分")

    result = []
    weights = {k: v for k, v in config.items() if isinstance(v, (int, float))}
    limit_score = config.get("limit_score", 7.0)
    conditional_dividend = config.get("dividend_weight_conditional", False)
    suppress_low_volume = config.get("suppress_low_volume", True)
    promote_large_cap = config.get("promote_large_cap", True)

    for _, row in df.iterrows():
        score = 0.0
        reasons = []
        suggestion = ""
        label = "👀 觀察股"

        stock_id = row["stock_id"]
        stock_name = row.get("stock_name", "")
        is_etf = str(row.get("is_etf", "")).lower() == "true"

        # --- 技術評分 ---
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

        # --- 基本面評分 ---
        buy_total = row.get("buy_total", 0) or 0
        eps_growth = row.get("eps_growth", False)
        dividend_yield = row.get("dividend_yield", 0) or 0

        if buy_total > 0:
            score += weights.get("buy_total", 0)
            reasons.append("法人買超")

        if eps_growth:
            score += weights.get("eps_growth", 0)
            reasons.append("EPS成長")

        # --- 殖利率加分（條件式） ---
        if dividend_yield >= 3 and row.get("ytd_return", 0) > 0:
            if is_etf:  # ETF 例外條件：不需 EPS
                score += weights.get("dividend_yield", 0)
                reasons.append("高殖利率（ETF）")
            elif conditional_dividend:
                if eps_growth or buy_total > 0:
                    score += weights.get("dividend_yield", 0)
                    reasons.append("高殖利率")
                else:
                    score += weights.get("dividend_yield", 0) * 0.2
                    reasons.append("高殖利率（未達基本面條件）")
            else:
                score += weights.get("dividend_yield", 0)
                reasons.append("高殖利率")

        # --- 冷門股降分、小型股補貼 ---
        if suppress_low_volume and (
            row.get("avg_volume", 0) < 1000 or row.get("market_cap", 0) < 10_000_000_000
        ):
            score *= 0.85
            reasons.append("流動性低調降分")

        if promote_large_cap and (
            row.get("avg_volume", 0) > 5000 and row.get("market_cap", 0) > 50_000_000_000
        ):
            score += 0.3
            reasons.append("大型股加分")

        # --- 分數限制 ---
        score = min(score, limit_score)
        rounded_score = round(score, 2)

        # --- 白話建議優化（新分數段） ---
        if rounded_score >= 6:
            suggestion = "建議立即列入關注清單"
            label = "✅ 推薦股"
        elif rounded_score >= 4.5:
            suggestion = "建議密切觀察（指標強但略有疑慮）"
        elif rounded_score >= 3:
            suggestion = "技術轉強但籌碼或流動性不足，保守觀望"
        else:
            suggestion = "不建議操作"

        result.append({
            "stock_id": stock_id,
            "stock_name": stock_name,
            "score": rounded_score,
            "reasons": "、".join(reasons),
            "suggestion": suggestion,
            "label": label
        })

    df_result = pd.DataFrame(result)
    print("[ta_analysis] 🧮 平均分數：", df_result["score"].mean())
    return df_result
