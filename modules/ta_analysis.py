# ta_analysis.py（含完整 debug 版本）
import pandas as pd
import numpy as np

def calculate_technical_scores(df):
    result = []
    
    for _, row in df.iterrows():
        score = 0
        reasons = []
        suggestion = "建議觀察"

        print(f"[ta_analysis] 分析 {row['stock_id']} {row.get('stock_name', '')}")

        # MACD 黃金交叉
        if row.get("macd_hist", 0) > 0 and row.get("macd", 0) > row.get("signal", 0):
            score += 2.0
            reasons.append("MACD黃金交叉")
            print("  ✅ 命中 MACD 黃金交叉")

        # KD 黃金交叉且低檔
        if row.get("kdj_k", 0) > row.get("kdj_d", 0) and row.get("kdj_k", 0) < 40:
            score += 2.0
            reasons.append("KD黃金交叉")
            print("  ✅ 命中 KD 黃金交叉")

        # RSI 上升且大於 50
        if row.get("rsi_14", 0) > 50 and row.get("rsi_14", 0) > row.get("rsi_14_prev", 0):
            score += 1.5
            reasons.append("RSI走強")
            print("  ✅ 命中 RSI 走強")

        # 股價高於均線
        ma_list = [row.get("close", 0) > row.get(f"ma{i}", 0) for i in [5, 20, 60]]
        if all(ma_list):
            score += 2.0
            reasons.append("站上均線")
            print("  ✅ 命中 均線多頭排列")

        # 布林通道：突破中線向上
        if row.get("close", 0) > row.get("bb_middle", 0):
            score += 1.5
            reasons.append("布林中線上揚")
            print("  ✅ 命中 布林通道")

        # 法人籌碼
        if row.get("buy_total", 0) > 0:
            score += 0.5
            reasons.append("法人買超")
            print("  ✅ 命中 法人買超")

        # EPS 成長
        if row.get("eps_growth", False):
            score += 0.5
            reasons.append("EPS成長")
            print("  ✅ 命中 EPS 成長")

        # 殖利率 + 報酬率
        if row.get("dividend_yield", 0) >= 3 and row.get("ytd_return", 0) > 0:
            score += 0.5
            reasons.append("高殖利率")
            print("  ✅ 命中 高殖利率")

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
