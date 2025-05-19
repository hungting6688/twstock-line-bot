"""
報告生成模組 - 整合 run_opening.py, intraday_monitor.py, dividend.py, closing_summary.py
"""
print("[reports] ✅ 已載入最新版")

from datetime import datetime
from modules.notification.line_bot import send_line_bot_message
from modules.analysis.technical import analyze_technical_indicators
from modules.data.fetcher import get_top_stocks
from modules.analysis.recommender import get_stock_recommendations, get_weak_valley_alerts

def analyze_opening():
    """
    執行開盤前分析
    """
    print("[reports] ⏳ 執行開盤前分析...")

    try:
        # 使用推薦模組獲取開盤前推薦，限制推薦數量
        stocks = get_stock_recommendations('morning', 6)  # 6檔推薦股票
        weak_valleys = get_weak_valley_alerts(2)  # 2檔極弱谷股票
        
        # 生成報告
        now = datetime.now().strftime("%Y/%m/%d")
        message = f"📈 {now} 09:00 開盤前分析\n\n"

        if stocks:
            message += "✅ 推薦股：\n"
            for stock in stocks:
                message += f"🔹 {stock['code']} {stock['name']}\n"
                message += f"推薦理由: {stock['reason']}\n"
                message += f"目標價: {stock['target_price']} | 止損價: {stock['stop_loss']}\n\n"
        else:
            message += "✅ 推薦股：無\n\n"

        if weak_valleys:
            message += "⚠️ 極弱谷警報：\n"
            for stock in weak_valleys:
                message += f"❗ {stock['code']} {stock['name']}\n"
                message += f"警報原因: {stock['alert_reason']}\n"
                message += f"當前價格: {stock['current_price']}\n\n"

        send_line_bot_message(message.strip())
        print("[reports] ✅ 開盤前分析完成")
        
    except Exception as e:
        error_message = f"[reports] ❌ 開盤前分析失敗：{str(e)}"
        print(error_message)
        send_line_bot_message(error_message)


def analyze_intraday():
    """
    執行盤中監控分析
    """
    print("[reports] ⏳ 執行盤中分析...")

    try:
        # 獲取盤中推薦股票，限制推薦數量
        stocks = get_stock_recommendations('noon', 6)  # 6檔推薦股票
        weak_valleys = get_weak_valley_alerts(2)  # 2檔極弱谷股票
        
        # 生成報告
        now = datetime.now().strftime("%Y/%m/%d")
        message = f"📊 {now} 10:30 盤中分析報告\n\n"

        if stocks:
            message += "✅ 盤中機會：\n"
            for stock in stocks:
                message += f"🔹 {stock['code']} {stock['name']}\n"
                message += f"理由: {stock['reason']}\n"
                message += f"目標價: {stock['target_price']} | 止損價: {stock['stop_loss']}\n\n"
        else:
            message += "✅ 盤中機會：無\n\n"

        if weak_valleys:
            message += "⚠️ 極弱谷警報：\n"
            for stock in weak_valleys:
                message += f"❗ {stock['code']} {stock['name']}\n"
                message += f"警報原因: {stock['alert_reason']}\n"
                message += f"當前價格: {stock['current_price']}\n\n"

        send_line_bot_message(message.strip())
        print("[reports] ✅ 盤中分析完成")
        
    except Exception as e:
        error_message = f"[reports] ❌ 盤中分析失敗：{str(e)}"
        print(error_message)
        send_line_bot_message(error_message)


def analyze_dividend():
    """
    執行配息潛力股分析
    """
    print("[reports] ⏳ 執行配息分析...")

    try:
        # 獲取高息股資料
        from modules.data.scraper import get_eps_data, get_dividend_data
        eps_data = get_eps_data()
        dividend_data = get_dividend_data()
        
        # 篩選高息股，但限制分析的股票數量
        # 只從前200檔股票中尋找高息股
        top_stocks = get_top_stocks(limit=200)
        high_dividend_stocks = []
        
        for sid in top_stocks:
            if sid in dividend_data and dividend_data[sid] >= 4.0:  # 殖利率 >= 4% 視為高息股
                try:
                    # 獲取股票名稱和其他資料
                    import yfinance as yf
                    ticker = yf.Ticker(f"{sid}.TW")
                    info = ticker.info
                    name = info.get('shortName', sid)
                    
                    # 獲取 EPS
                    eps = eps_data.get(sid, {}).get("eps", None)
                    
                    # 計算配息穩定性指數 (假設 EPS > 股息為穩定)
                    stability = "穩定" if eps and eps > dividend_data[sid] else "風險"
                    
                    high_dividend_stocks.append({
                        "stock_id": sid,
                        "name": name,
                        "dividend": dividend_data[sid],
                        "eps": eps,
                        "stability": stability
                    })
                except:
                    continue
        
        # 排序並限制數量至10檔
        high_dividend_stocks.sort(key=lambda x: x["dividend"], reverse=True)
        high_dividend_stocks = high_dividend_stocks[:10]
        
        # 生成報告
        now = datetime.now().strftime("%Y/%m/%d")
        message = f"💰 {now} 12:00 高息股報告\n\n"
        
        if high_dividend_stocks:
            message += "✅ 高息潛力股：\n"
            for stock in high_dividend_stocks:
                eps_text = f"，EPS: {stock['eps']}" if stock['eps'] else ""
                message += f"🔹 {stock['stock_id']} {stock['name']}｜殖利率: {stock['dividend']}%{eps_text}\n"
                message += f"➡️ 配息評估: {stock['stability']}\n\n"
        else:
            message += "無符合條件的高息股"

        send_line_bot_message(message.strip())
        print("[reports] ✅ 配息分析完成")
        
    except Exception as e:
        error_message = f"[reports] ❌ 配息分析失敗：{str(e)}"
        print(error_message)
        send_line_bot_message(error_message)


def analyze_closing():
    """
    執行收盤分析
    """
    print("[reports] ⏳ 執行收盤分析...")

    try:
        # 使用推薦模組獲取收盤後推薦，限制為10檔
        stocks = get_stock_recommendations('evening', 10)
        
        # 生成報告
        now = datetime.now().strftime("%Y/%m/%d")
        message = f"📉 {now} 15:00 收盤總結分析\n\n"

        if stocks:
            message += "✅ 明日關注股：\n"
            for stock in stocks:
                message += f"🔹 {stock['code']} {stock['name']}\n"
                message += f"理由: {stock['reason']}\n"
                message += f"目標價: {stock['target_price']} | 止損價: {stock['stop_loss']}\n\n"
        else:
            message += "✅ 明日關注股：無\n\n"

        # 獲取市場情緒評分
        from modules.analysis.sentiment import get_market_sentiment_score
        market_score = get_market_sentiment_score()
        
        # 生成市場情緒描述
        if market_score >= 8:
            sentiment_desc = "市場情緒非常樂觀，可適度加碼"
        elif market_score >= 6:
            sentiment_desc = "市場情緒偏向樂觀，可持股觀望"
        elif market_score >= 4:
            sentiment_desc = "市場情緒中性，建議謹慎操作"
        elif market_score >= 2:
            sentiment_desc = "市場情緒偏向悲觀，建議減碼保守"
        else:
            sentiment_desc = "市場情緒非常悲觀，建議暫時觀望"
            
        message += f"📊 市場情緒評分：{market_score}/10\n"
        message += f"💡 策略建議：{sentiment_desc}"

        send_line_bot_message(message.strip())
        print("[reports] ✅ 收盤分析完成")
        
    except Exception as e:
        error_message = f"[reports] ❌ 收盤分析失敗：{str(e)}"
        print(error_message)
        send_line_bot_message(error_message)
