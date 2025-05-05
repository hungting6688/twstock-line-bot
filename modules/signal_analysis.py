import pandas as pd
from modules.price_fetcher import get_price_data
from modules.ta_analysis import apply_all_indicators
from modules.eps_dividend_scraper import fetch_twse_eps_dividend

def analyze_stocks_with_signals(title="📈 推薦股分析", limit=100, min_score=2.0, filter_type="all"):
    stock_ids = get_default_hot_stock_ids(limit)

    # 基本面資料一次抓取
    df_fundamentals = fetch_twse_eps_dividend()

    results = []
    for stock_id in stock_ids:
        price_df = get_price_data(stock_id)
        if price_df.empty or len(price_df) < 30:
            continue

        df = apply_all_indicators(price_df)
        latest = df.iloc[-1]

        score = 0
        reasons = []

        # === 技術分析評分邏輯（含白話建議）===
        if latest["RSI6"] < 30:
            score += 1.0
            reasons.append("🟢 RSI < 30 超跌區，股價可能有反彈機會，可觀察是否止穩回升")

        if latest["K"] > latest["D"]:
            score += 1.0
            reasons.append("🟢 KD 黃金交叉，短線技術轉強，可關注是否進入多頭格局")

        if latest["MA5"] > latest["MA20"]:
            score += 1.0
            reasons.append("🟢 短均穿越長均（MA5 > MA20），顯示趨勢翻多，盤勢有機會向上延伸")

        if latest["MACD"] > latest["MACD_signal"]:
            score += 1.0
            reasons.append("🟢 MACD 多頭排列，動能轉強，若量能配合可考慮短期布局")

        if latest["close"] < latest["BOLL_lower"]:
            score += 1.0
            reasons.append("🟢 跌破布林下緣，短線可能超跌，有機會反彈，可設停損觀察")

        # === 基本面評分（來自 TWSE，含白話建議）===
        row = df_fundamentals[df_fundamentals["stock_id"] == stock_id]
        if not row.empty:
            row = row.iloc[0]
            try:
                if float(row["dividend_yield"]) > 5:
                    score += 1.0
                    reasons.append("🟢 殖利率 > 5%，具備長期收益潛力，適合關注存股族標的")

                if float(row["eps"]) > 3:
                    score += 1.0
                    reasons.append("🟢 EPS > 3 元，獲利穩健，基本面佳，可中長期關注")

                if float(row["pb_ratio"]) < 2:
                    score += 0.5
                    reasons.append("🟢 淨值比 < 2，股價相對淨值偏低，有基本面低估的機會")
            except:
                pass

        results.append({
            "stock_id": stock_id,
            "score": score,
            "reasons": reasons
        })

    if not results:
        return f"{title}\n⚠️ 今日無分析結果（資料不足或皆不符條件）"

    # 依分數排序
    df_result = pd.DataFrame(results)
    df_result = df_result.sort_values(by="score", ascending=False)

    # 推薦股
    recommended = df_result[df_result["score"] >= min_score]
    observe = df_result.head(3)

    msg = f"{title}\n"
    if not recommended.empty:
        msg += "\n✅ 推薦股：\n"
        for _, row in recommended.iterrows():
            reasons = "；".join(row["reasons"])
            msg += f"🔸 {row['stock_id']}（{row['score']} 分）\n{reasons}\n"
    else:
        msg += "\n⚠️ 今日無符合推薦分數門檻之股票。\n"

    msg += "\n📌 技術觀察股（分數最高前三名）：\n"
    for _, row in observe.iterrows():
        reasons = "；".join(row["reasons"])
        msg += f"🔹 {row['stock_id']}（{row['score']} 分）\n{reasons}\n"

    return msg.strip()


def get_default_hot_stock_ids(limit=100):
    return [
        "2330", "2317", "2303", "2603", "3711", "2881", "2454", "2609", "3231",
        "1513", "3707", "8046", "3034", "1101", "1301", "2002", "2882", "2891",
        "2409", "2615", "6147", "8261", "3045", "2344", "4919", "2605", "2408"
    ][:limit]
