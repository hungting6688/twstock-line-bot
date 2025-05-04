from modules.finmind_utils import fetch_finmind_data
from modules.run_opening import get_latest_valid_trading_date

def analyze_technical(stock_id="2330"):
    today = get_latest_valid_trading_date()
    df = fetch_finmind_data(
        dataset="TaiwanStockPrice",
        params={"stock_id": stock_id, "start_date": "2024-01-01", "end_date": today}
    )
    if df.empty or len(df) < 20:
        return f"【技術面】{stock_id}\n⚠️ 無法取得足夠資料"

    df["MA5"] = df["close"].rolling(5).mean()
    df["MA20"] = df["close"].rolling(20).mean()

    ma5 = df["MA5"].iloc[-1]
    ma20 = df["MA20"].iloc[-1]
    current = df["close"].iloc[-1]

    signal = "🟢 多頭排列，有機會續漲" if ma5 > ma20 and current > ma5 else "🔻 技術面偏弱，建議觀望"

    return (
        f"【收盤技術分析】{stock_id}\n"
        f"收盤價：{current}\n"
        f"5日均線：{round(ma5, 2)}\n"
        f"20日均線：{round(ma20, 2)}\n"
        f"判斷：{signal}"
    )
