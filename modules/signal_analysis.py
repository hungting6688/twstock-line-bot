import os
from datetime import datetime
from modules.finmind_utils import get_latest_valid_trading_date, fetch_finmind_data, get_hot_stock_ids
from google.oauth2.service_account import Credentials
import gspread
import json
from base64 import b64decode

def get_sheet_tracking_stocks():
    try:
        sheet_key = os.getenv("GOOGLE_SHEET_ID")
        json_key = os.getenv("GOOGLE_JSON_KEY")
        if not (sheet_key and json_key):
            return []
        info = json.loads(b64decode(json_key))
        creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(sheet_key).sheet1
        values = sheet.col_values(1)[1:]  # 忽略第一列標題
        return [v.strip() for v in values if v.strip()]
    except Exception as e:
        print(f"❌ Google Sheet 讀取失敗：{e}")
        return []

def analyze_stocks_with_signals(title="📊 推薦股報告", limit=100):
    hot_ids = get_hot_stock_ids(limit=limit)
    extra_ids = get_sheet_tracking_stocks()
    stock_ids = list(set(hot_ids + extra_ids))
    date = get_latest_valid_trading_date()
    results = []

    for sid in stock_ids:
        try:
            df = fetch_finmind_data(stock_id=sid, start_date="2024-01-01", end_date=date)
            if df is None or df.empty or "close" not in df.columns:
                print(f"⚠️ FinMind 無資料：{sid}")
                continue

            latest = df.iloc[-1]
            close = latest["close"]
            signals = []
            score = 0

            # 技術指標
            rsi = latest.get("rsi_6", 50)
            k = latest.get("kdj_k_9_3", 50)
            d = latest.get("kdj_d_9_3", 50)
            ma5 = latest.get("ma_5", close)
            ma20 = latest.get("ma_20", close)
            dif = latest.get("macd_dif_12_26_9", 0)
            macd = latest.get("macd_macd_12_26_9", 0)
            upper = latest.get("bolling_upper", close)
            lower = latest.get("bolling_lower", close)
            high = latest.get("high", close)
            low = latest.get("low", close)

            # RSI
            if rsi < 30:
                signals.append("🟢 RSI < 30 超跌區，留意反彈（反彈潛力）")
                score += 1
            elif rsi > 70:
                signals.append("🔺 RSI > 70 過熱，留意拉回（過熱預警）")

            # KD
            if k > d:
                signals.append("🟢 KD 黃金交叉，技術轉強（多頭訊號）")
                score += 1
            elif k < d:
                signals.append("🔻 KD 死亡交叉，動能轉弱（空頭風險）")
            if k < 20:
                signals.append("📉 K 值超賣，反彈契機（反彈潛力）")
                score += 1

            # 均線
            if ma5 > ma20:
                signals.append("🟢 短均穿越長均，趨勢翻多（多頭訊號）")
                score += 1
            elif ma5 < ma20:
                signals.append("🔻 均線空頭排列，趨勢轉弱（空頭風險）")

            # MACD
            if dif > macd and df["macd_dif_12_26_9"].iloc[-2] < df["macd_macd_12_26_9"].iloc[-2]:
                signals.append("🟢 MACD 黃金交叉，動能轉強（多頭訊號）")
                score += 1
            elif dif < macd and df["macd_dif_12_26_9"].iloc[-2] > df["macd_macd_12_26_9"].iloc[-2]:
                signals.append("🔻 MACD 死亡交叉，轉弱訊號（空頭風險）")

            # 布林通道
            if close <= lower * 1.02:
                signals.append("📉 接近布林下緣，低檔觀察（反彈潛力）")
                score += 1
            if close >= upper * 0.99:
                signals.append("📈 突破布林上軌，短線強勢（過熱預警）")

            # 收盤價分析
            if close == high:
                signals.append("🟢 收盤收最高，多方力道強（多頭訊號）")
                score += 1
            elif close == low:
                signals.append("🔻 收盤收最低，空方力道強（空頭風險）")

            if signals:
                results.append({
                    "stock_id": sid,
                    "score": score,
                    "signals": signals
                })

        except Exception as e:
            print(f"❌ 處理 {sid} 失敗：{e}")

    if not results:
        return f"{title}\n今日無符合條件的推薦股。"

    sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
    lines = [f"{title}"]
    for item in sorted_results:
        lines.append(f"【{item['stock_id']}】\n" + "\n".join(item["signals"]) + f"\n⭐️ 訊號分數：{item['score']}\n")

    return "\n".join(lines)
