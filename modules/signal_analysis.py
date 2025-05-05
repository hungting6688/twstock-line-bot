# modules/signal_analysis.py

from modules.price_fetcher import fetch_price_data
from modules.eps_dividend_scraper import fetch_eps_dividend_info
from modules.stock_data_utils import get_latest_valid_trading_date
import pandas as pd

# 評分規則與技術指標判斷
def analyze_stocks_with_signals(title, stock_ids, min_score=2.0):
    date = get_latest_valid_trading_date()
    eps_data = fetch_eps_dividend_info()
    results = []

    for stock_id in stock_ids:
        price_df = fetch_price_data(stock_id)
        if price_df is None or len(price_df) < 30:
            continue

        price_df = price_df.sort_values("Date", ascending=True).reset_index(drop=True)
        latest = price_df.iloc[-1]
        signals = []
        score = 0

        # RSI 判斷（超跌反彈機會）
        price_df["rsi6"] = price_df["close"].rolling(window=6).mean()
        if price_df["rsi6"].iloc[-1] < 30:
            score += 1.0
            signals.append("🟢 RSI < 30（超跌）")

        # KD 黃金交叉
        low9 = price_df["low"].rolling(window=9).min()
        high9 = price_df["high"].rolling(window=9).max()
        rsv = (price_df["close"] - low9) / (high9 - low9) * 100
        k = rsv.ewm(com=2).mean()
        d = k.ewm(com=2).mean()
        if k.iloc[-2] < d.iloc[-2] and k.iloc[-1] > d.iloc[-1]:
            score += 1.0
            signals.append("🟢 KD 黃金交叉")

        # 均線穿越
        price_df["ma5"] = price_df["close"].rolling(window=5).mean()
        price_df["ma20"] = price_df["close"].rolling(window=20).mean()
        if price_df["ma5"].iloc[-2] < price_df["ma20"].iloc[-2] and price_df["ma5"].iloc[-1] > price_df["ma20"].iloc[-1]:
            score += 1.0
            signals.append("🟢 MA5 上穿 MA20")

        # MACD
        ema12 = price_df["close"].ewm(span=12).mean()
        ema26 = price_df["close"].ewm(span=26).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9).mean()
        if macd_line.iloc[-2] < signal_line.iloc[-2] and macd_line.iloc[-1] > signal_line.iloc[-1]:
            score += 1.0
            signals.append("🟢 MACD 黃金交叉")

        # 布林通道 - 突破下軌
        ma20 = price_df["close"].rolling(window=20).mean()
        std = price_df["close"].rolling(window=20).std()
        lower = ma20 - 2 * std
        if price_df["close"].iloc[-1] < lower.iloc[-1]:
            score += 0.5
            signals.append("🟡 跌破布林下緣")

        # 基本面 EPS
        eps_info = eps_data.get(stock_id, {})
        if eps_info.get("EPS", 0) >= 2:
            score += 0.5
            signals.append(f"🟢 EPS {eps_info['EPS']}")

        # 殖利率
        if eps_info.get("殖利率", 0) >= 5:
            score += 0.5
            signals.append(f"🟢 殖利率 {eps_info['殖利率']}%")

        # 分數紀錄
        if score >= min_score:
            results.append((stock_id, score, signals))

    if not results:
        return f"{title}\n⚠️ 今日無推薦股票（符合條件者）。"

    # 排序與輸出
    results = sorted(results, key=lambda x: x[1], reverse=True)
    msg = f"{title}\n"
    for stock_id, score, sig in results[:5]:
        sig_text = "\n  - ".join(sig)
        msg += f"\n🔹 {stock_id}（分數：{score:.1f}）\n  - {sig_text}\n"

    return msg.strip()
