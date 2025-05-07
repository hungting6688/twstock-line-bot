# modules/ta_analysis.py

import pandas as pd

def calculate_technical_scores(df):
    print("[ta_analysis] ✅ 開始評分")
    result = []
    for _, row in df.iterrows():
        score = 0.0
        reasons = []
        suggestion = ""

        # 直接從原始欄位判斷各項技術指標
        if row.get("macd_hist", 0) > 0 and row.get("macd", 0) > row.get("signal", 0):
            score += 2
            reasons.append("MACD黃金交叉")
        if row.get("kdj_k", 0) > row.get("kdj_d", 0) and row.get("kdj_k", 0) < 40:
            score += 2
            reasons.append("KD黃金交叉")
        if row.get("rsi_14", 0) > 50 and row.get("rsi_14", 0) > row.get("rsi_14_prev", 0):
            score += 1.5
            reasons.append("RSI走強")
        if all([
            row.get("close", 0) > row.get("ma5", 0),
            row.get("close", 0) > row.get("ma20", 0),
            row.get("close", 0) > row.get("ma60", 0)
        ]):
            score += 2
            reasons.append("站上均線")
        if row.get("close", 0) > row.get("bb_middle", 0):
            score += 1.5
            reasons.append("布林通道偏多")
        if row.get("buy_total", 0) > 0:
            score += 0.5
            reasons.append("法人買超")
        if row.get("eps_growth", False):
            score += 0.5
            reasons.append("EPS成長")
        if row.get("dividend_yield", 0) >= 3 and row.get("ytd_return", 0) > 0:
            score += 0.5
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
