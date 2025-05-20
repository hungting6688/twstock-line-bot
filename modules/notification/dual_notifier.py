"""
雙重通知模組 - 支持發送電子郵件和LINE通知
"""
import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# 直接定義 NOTIFICATION_CONFIG 配置
NOTIFICATION_CONFIG = {
    'email': {
        'smtp_server': os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('EMAIL_SMTP_PORT', '587')),
        'user': os.getenv('EMAIL_SENDER'),
        'password': os.getenv('EMAIL_PASSWORD'),
        'to': os.getenv('EMAIL_RECEIVER')
    },
    'line': {
        'token': os.getenv('LINE_CHANNEL_ACCESS_TOKEN'),
        'user_id': os.getenv('LINE_USER_ID')
    }
}

def send_notification(message, subject, html_body=None):
    """
    發送通知(郵件和LINE)
    
    參數:
    - message: 通知文本內容
    - subject: 郵件主題
    - html_body: HTML格式的郵件正文(可選)
    """
    # 發送電子郵件
    send_email(message, subject, html_body)
    
    # 發送LINE通知
    send_line_notify(message)


def send_email(message, subject, html_body=None):
    """
    發送電子郵件通知
    
    參數:
    - message: 郵件文本內容
    - subject: 郵件主題
    - html_body: HTML格式的郵件正文(可選)
    """
    try:
        # 獲取郵件設置
        email_config = NOTIFICATION_CONFIG.get('email', {})
        smtp_server = email_config.get('smtp_server')
        smtp_port = email_config.get('smtp_port')
        smtp_user = email_config.get('user')
        smtp_password = email_config.get('password')
        email_to = email_config.get('to')
        
        if not all([smtp_server, smtp_port, smtp_user, smtp_password, email_to]):
            print("[dual_notifier] ⚠️ 郵件設置不完整，跳過發送")
            return False
        
        # 創建郵件物件
        if html_body:
            msg = MIMEMultipart('alternative')
            text_part = MIMEText(message, 'plain', 'utf-8')
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(text_part)
            msg.attach(html_part)
        else:
            msg = MIMEMultipart()
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
        
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = email_to
        
        # 連接SMTP伺服器並發送
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        print("[dual_notifier] ✅ 郵件發送成功")
        return True
    except Exception as e:
        print(f"[dual_notifier] ❌ 郵件發送失敗: {e}")
        return False


def send_line_notify(message):
    """
    發送LINE Notify通知
    
    參數:
    - message: 通知文本內容
    """
    try:
        # 獲取LINE設置
        line_config = NOTIFICATION_CONFIG.get('line', {})
        token = line_config.get('token')
        
        if not token:
            print("[dual_notifier] ⚠️ LINE設置不完整，跳過發送")
            return False
        
        # 發送LINE通知
        url = 'https://notify-api.line.me/api/notify'
        headers = {'Authorization': f'Bearer {token}'}
        data = {'message': message}
        
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 200:
            print("[dual_notifier] ✅ LINE通知發送成功")
            return True
        else:
            print(f"[dual_notifier] ⚠️ LINE通知發送失敗: {response.text}")
            return False
    except Exception as e:
        print(f"[dual_notifier] ❌ LINE通知發送失敗: {e}")
        return False


def send_combined_recommendations(strategies_data, time_slot):
    """
    發送包含三種策略的股票推薦通知
    
    參數:
    - strategies_data: 包含三種策略的字典 {"short_term": [...], "long_term": [...], "weak_stocks": [...]}
    - time_slot: 時段名稱
    """
    short_term_stocks = strategies_data.get("short_term", [])
    long_term_stocks = strategies_data.get("long_term", [])
    weak_stocks = strategies_data.get("weak_stocks", [])
    
    if not short_term_stocks and not long_term_stocks and not weak_stocks:
        message = f"【{time_slot}分析報告】\n\n沒有符合條件的推薦股票和警示"
        subject = f"【{time_slot}分析報告】- 無推薦"
        send_notification(message, subject)
        return
    
    # 生成通知消息
    today = datetime.now().strftime("%Y/%m/%d")
    message = f"📈 {today} {time_slot}分析報告\n\n"
    
    # 短線推薦部分
    message += "【短線推薦】\n\n"
    if short_term_stocks:
        for stock in short_term_stocks:
            message += f"📈 {stock['code']} {stock['name']}\n"
            message += f"推薦理由: {stock['reason']}\n"
            message += f"目標價: {stock['target_price']} | 止損價: {stock['stop_loss']}\n\n"
    else:
        message += "今日無短線推薦股票\n\n"
    
    # 長線推薦部分
    message += "【長線潛力】\n\n"
    if long_term_stocks:
        for stock in long_term_stocks:
            message += f"📊 {stock['code']} {stock['name']}\n"
            message += f"推薦理由: {stock['reason']}\n"
            message += f"目標價: {stock['target_price']} | 止損價: {stock['stop_loss']}\n\n"
    else:
        message += "今日無長線推薦股票\n\n"
    
    # 極弱股警示部分
    message += "【極弱股】\n\n"
    if weak_stocks:
        for stock in weak_stocks:
            message += f"⚠️ {stock['code']} {stock['name']}\n"
            message += f"當前價格: {stock['current_price']}\n"
            message += f"警報原因: {stock['alert_reason']}\n\n"
    else:
        message += "今日無極弱股警示\n\n"
    
    # 生成 HTML 格式的電子郵件正文
    html_parts = []
    html_parts.append("""
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; }
            .header { color: #0066cc; font-size: 20px; font-weight: bold; margin-bottom: 20px; }
            .section { margin-bottom: 30px; }
            .section-title { color: #333; font-size: 18px; font-weight: bold; margin-bottom: 15px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
            .stock { margin-bottom: 20px; border-left: 4px solid #0066cc; padding-left: 15px; }
            .stock.long-term { border-left-color: #009900; }
            .stock.weak { border-left-color: #cc0000; }
            .stock-name { font-weight: bold; font-size: 16px; }
            .label { color: #666; }
            .price { color: #009900; font-weight: bold; }
            .stop-loss { color: #cc0000; font-weight: bold; }
            .current-price { font-weight: bold; }
            .reason { color: #333; }
            .footer { color: #666; font-size: 12px; margin-top: 30px; }
        </style>
    </head>
    <body>
        <div class="header">""" + f"📈 {today} {time_slot}分析報告" + """</div>
    """)
    
    # 短線推薦 HTML
    html_parts.append("""
        <div class="section">
            <div class="section-title">【短線推薦】</div>
    """)
    
    if short_term_stocks:
        for stock in short_term_stocks:
            stock_html = """
            <div class="stock">
                <div class="stock-name">📈 """ + stock['code'] + " " + stock['name'] + """</div>
                <div><span class="label">推薦理由:</span> <span class="reason">""" + stock['reason'] + """</span></div>
                <div><span class="label">目標價:</span> <span class="price">""" + str(stock['target_price']) + """</span> | <span class="label">止損價:</span> <span class="stop-loss">""" + str(stock['stop_loss']) + """</span></div>
                <div><span class="label">當前價格:</span> <span class="current-price">""" + str(stock.get('current_price', '無資料')) + """</span></div>
            </div>
            """
            html_parts.append(stock_html)
    else:
        html_parts.append("""<div>今日無短線推薦股票</div>""")
    
    html_parts.append("""</div>""")  # 關閉短線推薦區段
    
    # 長線推薦 HTML
    html_parts.append("""
        <div class="section">
            <div class="section-title">【長線潛力】</div>
    """)
    
    if long_term_stocks:
        for stock in long_term_stocks:
            stock_html = """
            <div class="stock long-term">
                <div class="stock-name">📊 """ + stock['code'] + " " + stock['name'] + """</div>
                <div><span class="label">推薦理由:</span> <span class="reason">""" + stock['reason'] + """</span></div>
                <div><span class="label">目標價:</span> <span class="price">""" + str(stock['target_price']) + """</span> | <span class="label">止損價:</span> <span class="stop-loss">""" + str(stock['stop_loss']) + """</span></div>
                <div><span class="label">當前價格:</span> <span class="current-price">""" + str(stock.get('current_price', '無資料')) + """</span></div>
            </div>
            """
            html_parts.append(stock_html)
    else:
        html_parts.append("""<div>今日無長線推薦股票</div>""")
    
    html_parts.append("""</div>""")  # 關閉長線推薦區段
    
    # 極弱股警示 HTML
    html_parts.append("""
        <div class="section">
            <div class="section-title">【極弱股】</div>
    """)
    
    if weak_stocks:
        for stock in weak_stocks:
            stock_html = """
            <div class="stock weak">
                <div class="stock-name">⚠️ """ + stock['code'] + " " + stock['name'] + """</div>
                <div><span class="label">當前價格:</span> <span class="current-price">""" + str(stock['current_price']) + """</span></div>
                <div><span class="label">警報原因:</span> <span class="reason">""" + stock['alert_reason'] + """</span></div>
            </div>
            """
            html_parts.append(stock_html)
    else:
        html_parts.append("""<div>今日無極弱股警示</div>""")
    
    html_parts.append("""</div>""")  # 關閉極弱股警示區段
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html_parts.append("""
        <div class="footer">
            此電子郵件由台股分析系統自動產生於 """ + timestamp + """
        </div>
    </body>
    </html>
    """)
    
    html_body = "".join(html_parts)
    subject = f"【{time_slot}分析報告】- {today}"
    send_notification(message, subject, html_body)


def send_stock_recommendations(stocks, time_slot):
    """
    發送單一策略股票推薦通知(舊版函數，保留向後兼容)
    
    參數:
    - stocks: 推薦股票列表
    - time_slot: 時段名稱
    """
    if not stocks:
        message = f"【{time_slot}推薦】\n\n沒有符合條件的推薦股票"
        subject = f"【{time_slot}推薦】- 無推薦"
        send_notification(message, subject)
        return
    
    # 生成通知消息
    today = datetime.now().strftime("%Y/%m/%d")
    message = f"📈 {today} {time_slot}推薦股票\n\n"
    
    for stock in stocks:
        message += f"📊 {stock['code']} {stock['name']}\n"
        message += f"推薦理由: {stock['reason']}\n"
        message += f"目標價: {stock['target_price']} | 止損價: {stock['stop_loss']}\n\n"
    
    # 生成 HTML 格式的電子郵件正文
    html_parts = []
    html_parts.append("""
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; }
            .header { color: #0066cc; font-size: 20px; font-weight: bold; margin-bottom: 20px; }
            .stock { margin-bottom: 20px; border-left: 4px solid #0066cc; padding-left: 15px; }
            .stock-name { font-weight: bold; font-size: 16px; }
            .label { color: #666; }
            .price { color: #009900; font-weight: bold; }
            .stop-loss { color: #cc0000; font-weight: bold; }
            .reason { color: #333; }
            .footer { color: #666; font-size: 12px; margin-top: 30px; }
        </style>
    </head>
    <body>
        <div class="header">""" + f"📈 {today} {time_slot}推薦股票" + """</div>
    """)
    
    for stock in stocks:
        stock_html = """
        <div class="stock">
            <div class="stock-name">📊 """ + stock['code'] + " " + stock['name'] + """</div>
            <div><span class="label">推薦理由:</span> <span class="reason">""" + stock['reason'] + """</span></div>
            <div><span class="label">目標價:</span> <span class="price">""" + str(stock['target_price']) + """</span> | <span class="label">止損價:</span> <span class="stop-loss">""" + str(stock['stop_loss']) + """</span></div>
        </div>
        """
        html_parts.append(stock_html)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html_parts.append("""
        <div class="footer">
            此電子郵件由台股分析系統自動產生於 """ + timestamp + """
        </div>
    </body>
    </html>
    """)
    
    html_body = "".join(html_parts)
    subject = f"【{time_slot}推薦】- {today}"
    send_notification(message, subject, html_body)


def send_weak_stock_alerts(stocks):
    """
    發送弱勢股警示通知(舊版函數，保留向後兼容)
    
    參數:
    - stocks: 弱勢股列表
    """
    if not stocks:
        message = "【極弱股警示】\n\n沒有極弱股警示"
        subject = "【極弱股警示】- 無警示"
        send_notification(message, subject)
        return
    
    # 生成通知消息
    today = datetime.now().strftime("%Y/%m/%d")
    message = f"⚠️ {today} 極弱股警示\n\n"
    
    for stock in stocks:
        message += f"⚠️ {stock['code']} {stock['name']}\n"
        message += f"當前價格: {stock['current_price']}\n"
        message += f"警報原因: {stock['alert_reason']}\n\n"
    
    # 生成 HTML 格式的電子郵件正文
    html_parts = []
    html_parts.append("""
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; }
            .header { color: #cc0000; font-size: 20px; font-weight: bold; margin-bottom: 20px; }
            .stock { margin-bottom: 20px; border-left: 4px solid #cc0000; padding-left: 15px; }
            .stock-name { font-weight: bold; font-size: 16px; }
            .label { color: #666; }
            .price { font-weight: bold; }
            .reason { color: #333; }
            .footer { color: #666; font-size: 12px; margin-top: 30px; }
        </style>
    </head>
    <body>
        <div class="header">""" + f"⚠️ {today} 極弱股警示" + """</div>
    """)
    
    for stock in stocks:
        stock_html = """
        <div class="stock">
            <div class="stock-name">⚠️ """ + stock['code'] + " " + stock['name'] + """</div>
            <div><span class="label">當前價格:</span> <span class="price">""" + str(stock['current_price']) + """</span></div>
            <div><span class="label">警報原因:</span> <span class="reason">""" + stock['alert_reason'] + """</span></div>
        </div>
        """
        html_parts.append(stock_html)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html_parts.append("""
        <div class="footer">
            此電子郵件由台股分析系統自動產生於 """ + timestamp + """
        </div>
    </body>
    </html>
    """)
    
    html_body = "".join(html_parts)
    subject = f"【極弱股警示】- {today}"
    send_notification(message, subject, html_body)
