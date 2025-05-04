from modules.finmind_utils import fetch_finmind_data
from datetime import datetime
from modules.run_opening import get_latest_valid_trading_date  # 共用日期工具

def analyze_dividend(stock_id="2330"):
    today = get_latest_valid_trading_date()
    df = fetch_finmind_data(
        dataset="TaiwanStockDividend",
        params={"stock_id": stock_id, "date": today}
    )
    if df.empty:
        return f"【股利分析】{stock_id}\n⚠️ 無法取得資料"

    latest = df.iloc[-1]
    return (
        f"【股利分析】{stock_id}\n"
        f"年度：{latest.get('year', '')}\n"
        f"現金股利：{latest.get('cash_dividend', '')}\n"
        f"殖利率：約 {latest.get('dividend_yield', '未知')}%\n"
    )
