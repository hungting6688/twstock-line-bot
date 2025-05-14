# ✅ ta_analysis.py

def score_technical_signals(df, strategy, sentiment_info=None):
    print("[ta_analysis] ✅ 開始評分")

    df = df.copy()
    score = pd.Series(0, index=df.index, dtype="float")
    reasons = [[] for _ in range(len(df))]

    def add_reason(i, condition, reason_text, weight):
        nonlocal score, reasons
        if condition:
            score[i] += weight
            reasons[i].append(reason_text)

    for i, row in df.iterrows():
        add_reason(i, row.get("macd_signal"), "MACD黃金交叉", strategy.get("macd", 1))
        add_reason(i, row.get("kdj_signal"), "KD黃金交叉", strategy.get("kdj", 0.5))
        add_reason(i, row.get("rsi_signal"), "RSI走強", strategy.get("rsi", 0.5))
        add_reason(i, row.get("ma_signal"), "站上均線", strategy.get("ma", 1))
        add_reason(i, row.get("bollinger_signal"), "布林通道偏多", strategy.get("bollinger", 0.5))

        # 基本面
        add_reason(i, row.get("eps_growth", 0) > 0, "EPS成長", strategy.get("eps_growth", 1))
        add_reason(i, row.get("buy_total", 0) > 0, "法人買超", strategy.get("buy_total", 1))

        # 殖利率加分條件
        if strategy.get("dividend_weight_conditional"):
            if row.get("buy_total", 0) > 0 and row.get("eps_growth", 0) > 0 and row.get("dividend_yield", 0) > 4:
                add_reason(i, True, "高殖利率", strategy.get("dividend_yield", 1))
        else:
            add_reason(i, row.get("dividend_yield", 0) > 4, "高殖利率", strategy.get("dividend_yield", 1))

        # 降分與加權
        if strategy.get("suppress_low_volume") and row.get("turnover", 0) < 1e8:
            score[i] -= 0.5
            reasons[i].append("流動性低調降分")

        if strategy.get("promote_large_cap") and row.get("cap_class", "") == "大型股":
            score[i] += 0.5
            reasons[i].append("大型股")

    # 情緒調整
    if sentiment_info:
        score *= sentiment_info.get("factor", 1.0)

    df["score"] = score.clip(0, strategy.get("limit_score", 7.0))
    df["reasons"] = ["、".join(r) if r else "-" for r in reasons]

    # 白話建議
    df["suggestion"] = df["score"].apply(lambda s: "建議立即列入關注清單" if s >= strategy.get("recommend_min", 6) else
                                         "建議密切觀察" if s >= strategy.get("min_score", 5) else
                                         "不建議操作")

    return df
