
from modules.finmind_utils import fetch_finmind_data, get_hot_stock_ids, get_latest_valid_trading_date
from datetime import datetime
import pandas as pd

# 技術指標規則與加權分數設定
TECH_SIGNAL_RULES = {
    "RSI_low": {"weight": 1.5, "condition": lambda x: x.get("rsi_6", 50) < 30, "text": "🟢 RSI < 30（超跌反彈）"},
    "RSI_high": {"weight": -1, "condition": lambda x: x.get("rsi_6", 50) > 70, "text": "🔴 RSI > 70（超買回檔）"},
    "KD_gc": {"weight": 2, "condition": lambda x: x.get("kdj_k_9_3", 50) > x.get("kdj_d_9_3", 50), "text": "🟢 KD 黃金交叉"},
    "KD_dc": {"weight": -1.5, "condition": lambda x: x.get("kdj_k_9_3", 50) < x.get("kdj_d_9_3", 50), "text": "🔴 KD 死亡交叉"},
    "MA_cross_up": {"weight": 1, "condition": lambda x: x.get("ma5", 0) > x.get("ma20", 0), "text": "🟢 MA5 > MA20（短期翻多）"},
    "MA_cross_down": {"weight": -1, "condition": lambda x: x.get("ma5", 0) < x.get("ma20", 0), "text": "🔴 MA5 < MA20（短期轉弱）"},
    "MACD_gc": {"weight": 2.5, "condition": lambda x: x.get("macd_dif_12_26_9", 0) > x.get("macd_macd_12_26_9", 0), "text": "🟢 MACD 翻多"},
    "MACD_dc": {"weight": -2, "condition": lambda x: x.get("macd_dif_12_26_9", 0) < x.get("macd_macd_12_26_9", 0), "text": "🔴 MACD 翻空"},
    "BOLL_low": {"weight": 1, "condition": lambda x: x.get("close", 0) < x.get("boll_lower", 0), "text": "🟢 收盤 < 下軌（偏低反彈）"},
    "BOLL_high": {"weight": -1.5, "condition": lambda x: x.get("close", 0) > x.get("boll_upper", 0), "text": "🔴 收盤 > 上軌（偏高留意）"},
}

def evaluate_signals(latest_row):
    score = 0
    texts = []
    for key, rule in TECH_SIGNAL_RULES.items():
        try:
            if rule["condition"](latest_row):
                score += rule["weight"]
                texts.append(rule["text"])
        except:
            continue
    return round(score, 2), texts

def analyze_stocks_with_signals(title="📊 技術分析推薦", limit=100, min_score=2.0, filter_type="all"):
    date = get_latest_valid_trading_date()
    stock_ids = get_hot_stock_ids(limit=limit, filter_type=filter_type)
    results = []

    for stock_id in stock_ids:
        df = fetch_finmind_data(stock_id, start_date="2023-01-01", end_date=date)
        if df is None or df.empty or "close" not in df.columns:
            continue

        df["ma5"] = df["close"].rolling(5).mean()
        df["ma20"] = df["close"].rolling(20).mean()
        df["boll_middle"] = df["close"].rolling(20).mean()
        df["boll_std"] = df["close"].rolling(20).std()
        df["boll_upper"] = df["boll_middle"] + 2 * df["boll_std"]
        df["boll_lower"] = df["boll_middle"] - 2 * df["boll_std"]

        latest = df.iloc[-1].to_dict()
        score, signal_texts = evaluate_signals(latest)

        results.append({
            "stock_id": stock_id,
            "score": score,
            "signals": signal_texts
        })

    if not results:
        return f"{title}⚠️ 今日無法取得任何分析資料。"

    sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
    strong_stocks = [r for r in sorted_results if r["score"] >= min_score]

    msg = f"{title}
"

    if strong_stocks:
        msg += "✅ 推薦股：
"
        for idx, stock in enumerate(strong_stocks[:5]):
            signals = "、".join(stock["signals"])
            msg += f"{idx+1}. {stock['stock_id']}（總分 {stock['score']}）→ {signals}
"
    else:
        msg += "⚠️ 今日無強烈推薦股，以下為技術分數前 3 名觀察股：
"
        for idx, stock in enumerate(sorted_results[:3]):
            signals = "、".join(stock["signals"])
            msg += f"{idx+1}. {stock['stock_id']}（分數 {stock['score']}）→ {signals}
"

    return msg.strip()
