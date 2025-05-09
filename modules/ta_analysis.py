# ✅ 修正版 ta_analysis.py
import pandas as pd

def calculate_technical_scores(df, **weights):
    print("[ta_analysis] ✅ 開始評分")
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

        # 殖利率條件式加分（需搭配 eps 或 buy_total）
        div_yield = row.get("dividend_yield", 0)
        if div_yield >= 3:
            if weights.get("dividend_weight_conditional", False):
                if row.get("buy_total", 0) > 0 or row.get("eps_growth", False):
                    score += weights.get("dividend_yield", 0)
                    reasons.append("高殖利率")
            else:
                score += weights.get("dividend_yield", 0)
                reasons.append("高殖利率")

        # 冷門股降分（小市值或低成交量）
        if weights.get("suppress_low_volume", False):
            if row.get("avg_volume", 0) < 1000 or row.get("market_cap", 0) < 10_000_000_000:
                score -= 0.5
                reasons.append("流動性低調降分")

        # 大型股加分
        if weights.get("promote_large_cap", False):
            if row.get("avg_volume", 0) > 5000 and row.get("market_cap", 0) > 50_000_000_000:
                score += 0.5
                reasons.append("大型股加分")

        # 白話建議
        if score >= 6.5:
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
