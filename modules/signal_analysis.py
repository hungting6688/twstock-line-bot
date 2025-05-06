# modules/signal_analysis.py
print("[signal_analysis] ✅ 已載入最新版")
from modules.ta_analysis import analyze_technical_indicators
from modules.eps_dividend_scraper import get_eps_data
from modules.price_fetcher import get_top_stocks
from modules.line_bot import send_line_bot_message

def analyze_stocks_with_signals(
    limit: int = 100,
    min_score: float = 3,
    include_weak: bool = False,
    filter_type: str = None
) -> str:
    print(f"[signal] 開始分析前 {limit} 檔熱門股...")

    # 熱門股清單
    stock_ids = get_top_stocks(limit=limit, filter_type=filter_type)
    print(f"[signal] 取得 {len(stock_ids)} 檔股票進行分析")

    # 技術分析
    stock_results = analyze_technical_indicators(stock_ids)
    print(f"[signal] 技術分析完成 {len(stock_results)} 檔")

    # 基本面資料
    eps_data = get_eps_data()

    # 推薦與觀察分類
    recommended = []
    fallback = []
    for sid, result in stock_results.items():
        score = result["score"]
        suggestion = result["suggestion"]

        eps_info = eps_data.get(sid, {})
        eps_val = eps_info.get("eps")
        div_val = eps_info.get("dividend")
        eps_txt = ""
        if eps_val is not None:
            eps_txt += f" | EPS: {eps_val}"
        if div_val is not None:
            eps_txt += f" / 配息: {div_val}"

        line = f"{sid} | Score: {score} | {suggestion}{eps_txt}"

        if score >= min_score:
            recommended.append((score, line))
        else:
            fallback.append((score, line))

    # 排序與組裝推播文字
    lines = []
    if recommended:
        lines.append("✅ 推薦股票：")
        for _, line in sorted(recommended, key=lambda x: -x[0])[:5]:
            lines.append(line)
    else:
        lines.append("（無股票達推薦標準，列出觀察股）")
        for _, line in sorted(fallback, key=lambda x: -x[0])[:3]:
            lines.append(line)

    # 顯示極弱股
    if include_weak:
        weak_lines = []
        for sid, result in stock_results.items():
            if result.get("is_weak"):
                weak_lines.append(f"{sid} | RSI 過低 + 跌破均線，短線轉弱請留意風險。")
        if weak_lines:
            lines.append("\n⚠️ 極弱提醒：")
            lines += weak_lines[:5]

    return "📌 分析模式：intraday\n" + "\n".join(lines)
