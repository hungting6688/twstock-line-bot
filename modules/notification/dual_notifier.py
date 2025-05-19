"""
整合通知模組 - 同時支持 LINE 和電子郵件通知
"""
print("[dual_notifier] ✅ 已載入雙重通知模組")

# 導入 LINE 和電子郵件通知模組
from modules.notification.line_bot import send_line_bot_message
from modules.notification.email_notifier import send_email
from email.utils import formatdate
from datetime import datetime

def send_notification(message, subject=None, html_body=None):
    """
    同時發送 LINE 和電子郵件通知，無論 LINE 是否成功
    
    參數:
    - message: 通知內容
    - subject: 郵件主題 (可選，默認使用消息前20個字符)
    - html_body: HTML 格式郵件內容 (可選)
    
    返回:
    - dict: 各通知渠道的發送結果
    """
    results = {"line": False, "email": False}
    line_error = None
    
    # 嘗試發送 LINE 通知
    try:
        send_line_bot_message(message)
        results["line"] = True
        print("[dual_notifier] ✅ LINE 訊息推播成功")
    except Exception as e:
        line_error = str(e)
        # 檢查是否為月度限額錯誤
        if "429" in line_error or "monthly limit" in line_error.lower() or "reached your monthly limit" in line_error.lower():
            print(f"[dual_notifier] ⚠️ LINE Bot 已達到月度推送限額")
            
            # 將限額信息添加到電子郵件中
            if html_body:
                html_body += """
                <div style="margin-top: 20px; padding: 10px; background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; border-radius: 5px;">
                    <strong>注意：</strong> LINE Bot 已達到本月推送限額，通知暫時只能通過電子郵件發送。
                </div>
                """
        else:
            print(f"[dual_notifier] ⚠️ LINE 通知發送失敗: {e}")
    
    # 無論 LINE 是否成功，都發送電子郵件通知 (雙重通知)
    try:
        # 如果未指定主題，使用消息內容的前20個字符
        if not subject:
            if "\n" in message:
                subject = message.split("\n")[0][:50]  # 使用第一行作為主題
            else:
                subject = message[:50] + "..."  # 使用前50個字符
        
        send_email(subject, message, html_body)
        results["email"] = True
        print("[dual_notifier] ✅ 電子郵件通知發送成功")
    except Exception as e:
        print(f"[dual_notifier] ⚠️ 電子郵件通知發送失敗: {e}")
    
    # 輸出發送結果
    success_channels = [k for k, v in results.items() if v]
    if success_channels:
        print(f"[dual_notifier] ✅ 通知已成功發送至: {', '.join(success_channels)}")
    else:
        print(f"[dual_notifier] ❌ 所有通知渠道均發送失敗")
        if line_error:
            print(f"[dual_notifier] LINE 錯誤詳情: {line_error}")
    
    return results

def send_stock_recommendations(stocks, time_slot):
    """
    發送股票推薦通知
    
    參數:
    - stocks: 推薦股票列表
    - time_slot: 時段名稱
    """
    
    if not stocks:
        message = f"【{time_slot}推薦股票】\n\n沒有符合條件的推薦股票"
        subject = f"【{time_slot}推薦股票】- 無推薦"
        send_notification(message, subject)
        return
    
    # 生成通知消息
    message = f"【{time_slot}推薦股票】\n\n"
    for stock in stocks:
        message += f"📈 {stock['code']} {stock['name']}\n"
        message += f"推薦理由: {stock['reason']}\n"
        message += f"目標價: {stock['target_price']}\n"
        message += f"止損價: {stock['stop_loss']}\n\n"
    
    # 生成 HTML 格式的電子郵件正文
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            .header {{ color: #0066cc; font-size: 20px; font-weight: bold; margin-bottom: 20px; }}
            .stock {{ margin-bottom: 20px; border-left: 4px solid #0066cc; padding-left: 15px; }}
            .stock-name {{ font-weight: bold; font-size: 16px; }}
            .label {{ color: #666; }}
            .price {{ color: #009900; font-weight: bold; }}
            .stop-loss {{ color: #cc0000; font-weight: bold; }}
            .footer {{ color: #666; font-size: 12px; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="header">【{time_slot}推薦股票】- 共 {len(stocks)} 檔</div>
    """
    
    for stock in stocks:
        html_body += f"""
        <div class="stock">
            <div class="stock-name">📈 {stock['code']} {stock['name']}</div>
            <div><span class="label">推薦理由:</span> {stock['reason']}</div>
            <div><span class="label">目標價:</span> <span class="price">{stock['target_price']}</span></div>
            <div><span class="label">止損價:</span> <span class="stop-loss">{stock['stop_loss']}</span></div>
        </div>
        """
    
    html_body += f"""
        <div class="footer">
            此電子郵件由台股分析系統自動產生於 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </body>
    </html>
    """
    
    subject = f"【{time_slot}推薦股票】- {len(stocks)} 檔股票"
    send_notification(message, subject, html_body)

def send_weak_valley_alerts(weak_valleys):
    """
    發送極弱谷警報通知
    
    參數:
    - weak_valleys: 極弱谷股票列表
    """
    
    if not weak_valleys:
        return
    
    # 生成通知消息
    message = "【極弱谷警報】\n\n"
    for stock in weak_valleys:
        message += f"⚠️ {stock['code']} {stock['name']}\n"
        message += f"當前價格: {stock['current_price']}\n"
        message += f"警報原因: {stock['alert_reason']}\n\n"
    
    # 生成 HTML 格式的電子郵件正文
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            .header {{ color: #cc0000; font-size: 20px; font-weight: bold; margin-bottom: 20px; }}
            .stock {{ margin-bottom: 20px; border-left: 4px solid #cc0000; padding-left: 15px; }}
            .stock-name {{ font-weight: bold; font-size: 16px; }}
            .label {{ color: #666; }}
            .price {{ font-weight: bold; }}
            .reason {{ color: #cc0000; }}
            .footer {{ color: #666; font-size: 12px; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="header">【極弱谷警報】</div>
    """
    
    for stock in weak_valleys:
        html_body += f"""
        <div class="stock">
            <div class="stock-name">⚠️ {stock['code']} {stock['name']}</div>
            <div><span class="label">當前價格:</span> <span class="price">{stock['current_price']}</span></div>
            <div><span class="label">警報原因:</span> <span class="reason">{stock['alert_reason']}</span></div>
        </div>
        """
    
    html_body += f"""
        <div class="footer">
            此電子郵件由台股分析系統自動產生於 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </body>
    </html>
    """
    
    subject = f"【極弱谷警報】- {len(weak_valleys)} 檔股票"
    send_notification(message, subject, html_body)

def send_market_summary(market_score, top_performers, weak_performers):
    """
    發送市場總結通知
    
    參數:
    - market_score: 市場情緒得分 (0-10)
    - top_performers: 表現最佳的股票列表
    - weak_performers: 表現最差的股票列表
    """
    
    # 生成市場評估文字
    if market_score >= 8:
        market_status = "非常樂觀 🔥"
        market_advice = "市場氣氛熱絡，可考慮短線進場。"
    elif market_score >= 6:
        market_status = "偏向樂觀 📈"
        market_advice = "市場表現不錯，選股進場。"
    elif market_score >= 4:
        market_status = "中性 ⚖️"
        market_advice = "市場情緒平穩，謹慎操作為宜。"
    elif market_score >= 2:
        market_status = "偏向悲觀 📉"
        market_advice = "市場氣氛偏弱，建議減碼觀望。"
    else:
        market_status = "非常悲觀 ❄️"
        market_advice = "市場氣氛低迷，建議暫時觀望。"
    
    # 生成通知消息
    message = f"【每日市場總結】- {datetime.now().strftime('%Y/%m/%d')}\n\n"
    message += f"市場情緒評分: {market_score}/10 ({market_status})\n"
    message += f"建議策略: {market_advice}\n\n"
    
    if top_performers:
        message += "📊 今日表現最佳:\n"
        for stock in top_performers[:5]:  # 只顯示前5名
            message += f"🔹 {stock['code']} {stock['name']} ({stock['change']:+.2f}%)\n"
        message += "\n"
    
    if weak_performers:
        message += "📊 今日表現最弱:\n"
        for stock in weak_performers[:5]:  # 只顯示前5名
            message += f"🔸 {stock['code']} {stock['name']} ({stock['change']:+.2f}%)\n"
    
    # 生成 HTML 格式的電子郵件正文
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            .header {{ color: #333; font-size: 20px; font-weight: bold; margin-bottom: 20px; }}
            .market-info {{ margin-bottom: 20px; }}
            .market-score {{ font-size: 24px; font-weight: bold; }}
            .market-status {{ font-weight: bold; }}
            .market-status.positive {{ color: #009900; }}
            .market-status.neutral {{ color: #666; }}
            .market-status.negative {{ color: #cc0000; }}
            .advice {{ margin-top: 10px; font-style: italic; }}
            .section {{ margin-top: 20px; }}
            .section-title {{ font-weight: bold; margin-bottom: 10px; }}
            .stock {{ margin: 5px 0; }}
            .positive {{ color: #009900; }}
            .negative {{ color: #cc0000; }}
            .footer {{ color: #666; font-size: 12px; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="header">【每日市場總結】- {datetime.now().strftime('%Y/%m/%d')}</div>
        
        <div class="market-info">
            <div>市場情緒評分: <span class="market-score">{market_score}/10</span></div>
            <div>市場狀態: <span class="market-status {('positive' if market_score >= 6 else 'negative' if market_score <= 4 else 'neutral')}">{market_status}</span></div>
            <div class="advice">{market_advice}</div>
        </div>
    """
    
    if top_performers:
        html_body += """
        <div class="section">
            <div class="section-title">📊 今日表現最佳:</div>
        """
        for stock in top_performers[:5]:
            html_body += f"""
            <div class="stock">
                🔹 {stock['code']} {stock['name']} (<span class="positive">{stock['change']:+.2f}%</span>)
            </div>
            """
        html_body += "</div>"
    
    if weak_performers:
        html_body += """
        <div class="section">
            <div class="section-title">📊 今日表現最弱:</div>
        """
        for stock in weak_performers[:5]:
            html_body += f"""
            <div class="stock">
                🔸 {stock['code']} {stock['name']} (<span class="negative">{stock['change']:+.2f}%</span>)
            </div>
            """
        html_body += "</div>"
    
    html_body += f"""
        <div class="footer">
            此電子郵件由台股分析系統自動產生於 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </body>
    </html>
    """
    
    subject = f"【每日市場總結】- {datetime.now().strftime('%Y/%m/%d')} - 情緒指數 {market_score}/10"
    send_notification(message, subject, html_body)

# 測試雙重通知
