"""
modules/notification/dual_notifier.py 
雙重通知模組 - 支持發送電子郵件和LINE通知
增強版本 - 2025 年版本，強化錯誤處理和失敗重試機制
"""
import os
import smtplib
import requests
import time
import json
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# 確保日誌目錄存在
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# 通知設定
NOTIFICATION_CONFIG = {
    'email': {
        'smtp_server': os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('EMAIL_SMTP_PORT', '587')),
        'user': os.getenv('EMAIL_SENDER'),
        'password': os.getenv('EMAIL_PASSWORD'),
        'to': os.getenv('EMAIL_RECEIVER'),
        'retry_count': 3,
        'retry_delay': 5  # 秒
    },
    'line': {
        'token': os.getenv('LINE_CHANNEL_ACCESS_TOKEN'),
        'user_id': os.getenv('LINE_USER_ID'),
        'retry_count': 3,
        'retry_delay': 5  # 秒
    }
}

# 通知紀錄和狀態追蹤
NOTIFICATION_LOG = {
    'last_email_success': None,
    'last_line_success': None,
    'failed_attempts': {
        'email': 0,
        'line': 0
    }
}

def send_notification(message, subject, html_body=None, retry=True):
    """
    發送通知(郵件和LINE)，增加錯誤處理和重試機制
    
    參數:
    - message: 通知文本內容
    - subject: 郵件主題
    - html_body: HTML格式的郵件正文(可選)
    - retry: 是否啟用重試機制
    """
    # 嘗試發送電子郵件
    email_success = send_email(message, subject, html_body, retry)
    
    # 嘗試發送LINE通知
    line_success = send_line_notify(message, retry)
    
    # 如果兩種方式都失敗，寫入本地日誌
    if not email_success and not line_success:
        log_notification_failure(message, subject)
        return False
    
    return True

def send_email(message, subject, html_body=None, retry=True):
    """
    發送電子郵件通知，增加重試機制
    
    參數:
    - message: 郵件文本內容
    - subject: 郵件主題
    - html_body: HTML格式的郵件正文(可選)
    - retry: 是否啟用重試機制
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
            log_notification_event("郵件設置不完整，跳過發送", 'warning')
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
        
        # 增加重試邏輯
        max_retries = email_config.get('retry_count', 3) if retry else 1
        retry_delay = email_config.get('retry_delay', 5)  # 秒
        
        for attempt in range(max_retries):
            try:
                # 連接SMTP伺服器並發送
                if smtp_port == 465:
                    # SSL連接
                    with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30) as server:
                        server.login(smtp_user, smtp_password)
                        server.send_message(msg)
                else:
                    # 一般連接 (可能帶TLS)
                    with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                        server.starttls()
                        server.login(smtp_user, smtp_password)
                        server.send_message(msg)
                
                log_notification_event("郵件發送成功")
                NOTIFICATION_LOG['last_email_success'] = datetime.now().isoformat()
                NOTIFICATION_LOG['failed_attempts']['email'] = 0
                save_notification_log()
                return True
                
            except Exception as e:
                NOTIFICATION_LOG['failed_attempts']['email'] += 1
                
                if attempt < max_retries - 1:
                    log_notification_event(f"郵件發送失敗 (嘗試 {attempt+1}/{max_retries}): {e}", 'warning')
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指數退避策略
                else:
                    log_notification_event(f"郵件發送最終失敗: {e}", 'error')
                    
                    # 嘗試不同的SMTP連接方式
                    backup_result = try_alternative_smtp(msg, smtp_user, smtp_password, email_to)
                    save_notification_log()
                    return backup_result
        
    except Exception as e:
        log_notification_event(f"郵件發送發生異常: {e}", 'error')
        NOTIFICATION_LOG['failed_attempts']['email'] += 1
        save_notification_log()
        return False

def try_alternative_smtp(msg, smtp_user, smtp_password, email_to):
    """嘗試使用不同的SMTP設定發送郵件"""
    try:
        # 嘗試使用其他常見的SMTP設定
        log_notification_event("嘗試使用不同的SMTP設定...")
        
        if not all([smtp_user, smtp_password, email_to]):
            return False

        # Gmail 的備用端口和其他郵件服務
        alternate_settings = [
            ("smtp.gmail.com", 465, True),   # Gmail SSL
            ("smtp.gmail.com", 587, False),  # Gmail TLS
            ("smtp.mail.yahoo.com", 465, True),  # Yahoo Mail
            ("smtp-mail.outlook.com", 587, False),  # Outlook/Hotmail
        ]
        
        for server, port, use_ssl in alternate_settings:
            try:
                log_notification_event(f"嘗試連接 {server}:{port} (SSL: {use_ssl})")
                
                if use_ssl:
                    # SSL連接
                    with smtplib.SMTP_SSL(server, port, timeout=30) as smtp:
                        smtp.login(smtp_user, smtp_password)
                        smtp.send_message(msg)
                else:
                    # TLS連接
                    with smtplib.SMTP(server, port, timeout=30) as smtp:
                        smtp.starttls()
                        smtp.login(smtp_user, smtp_password)
                        smtp.send_message(msg)
                        
                log_notification_event(f"備用郵件伺服器 {server}:{port} 發送成功")
                return True
                
            except Exception as e:
                log_notification_event(f"備用伺服器 {server}:{port} 發送失敗: {e}", 'warning')
                
        return False
    except Exception as e:
        log_notification_event(f"嘗試備用SMTP服務失敗: {e}", 'error')
        return False

def send_line_notify(message, retry=True):
    """
    發送LINE Notify通知，增加重試機制
    
    參數:
    - message: 通知文本內容
    - retry: 是否啟用重試機制
    """
    try:
        # 獲取LINE設置
        line_config = NOTIFICATION_CONFIG.get('line', {})
        token = line_config.get('token')
        
        if not token:
            log_notification_event("LINE設置不完整，跳過發送", 'warning')
            return False
        
        # 增加重試邏輯
        max_retries = line_config.get('retry_count', 3) if retry else 1
        retry_delay = line_config.get('retry_delay', 5)  # 秒
        
        for attempt in range(max_retries):
            try:
                # 發送LINE通知
                url = 'https://notify-api.line.me/api/notify'
                headers = {'Authorization': f'Bearer {token}'}
                data = {'message': message}
                
                response = requests.post(url, headers=headers, data=data, timeout=30)
                
                if response.status_code == 200:
                    log_notification_event("LINE通知發送成功")
                    NOTIFICATION_LOG['last_line_success'] = datetime.now().isoformat()
                    NOTIFICATION_LOG['failed_attempts']['line'] = 0
                    save_notification_log()
                    return True
                else:
                    raise Exception(f"HTTP狀態碼: {response.status_code}, 回應: {response.text}")
                    
            except Exception as e:
                NOTIFICATION_LOG['failed_attempts']['line'] += 1
                
                if attempt < max_retries - 1:
                    log_notification_event(f"LINE通知發送失敗 (嘗試 {attempt+1}/{max_retries}): {e}", 'warning')
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指數退避策略
                else:
                    log_notification_event(f"LINE通知最終失敗: {e}", 'error')
                    save_notification_log()
                    return False
                    
    except Exception as e:
        log_notification_event(f"LINE通知發送發生異常: {e}", 'error')
        NOTIFICATION_LOG['failed_attempts']['line'] += 1
        save_notification_log()
        return False

def log_notification_failure(message, subject):
    """記錄發送失敗的通知到本地文件，以便後續重試"""
    try:
        log_file = os.path.join(LOG_DIR, 'failed_notifications.log')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"===== {timestamp} =====\n")
            f.write(f"主題: {subject}\n")
            f.write(f"內容:\n{message}\n")
            f.write("="*50 + "\n\n")
            
        log_notification_event(f"通知失敗，已記錄到 {log_file}")
    except Exception as e:
        log_notification_event(f"無法記錄失敗的通知: {e}", 'error')

def log_notification_event(message, level='info'):
    """記錄通知事件到日誌"""
    try:
        # 將消息輸出到控制台
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prefix = f"[dual_notifier] "
        
        if level == 'error':
            print(f"{prefix}❌ {message}")
        elif level == 'warning':
            print(f"{prefix}⚠️ {message}")
        else:
            print(f"{prefix}✅ {message}")
        
        # 寫入到日誌文件
        log_file = os.path.join(LOG_DIR, 'notifications.log')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{now} - {level.upper()} - {message}\n")
    except Exception as e:
        print(f"[dual_notifier] 無法記錄日誌: {e}")

def save_notification_log():
    """保存通知日誌狀態"""
    try:
        log_stats_file = os.path.join(LOG_DIR, 'notification_stats.json')
        with open(log_stats_file, 'w', encoding='utf-8') as f:
            json.dump(NOTIFICATION_LOG, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_notification_event(f"無法保存通知統計數據: {e}", 'warning')

def load_notification_log():
    """載入通知日誌狀態"""
    try:
        log_stats_file = os.path.join(LOG_DIR, 'notification_stats.json')
        if os.path.exists(log_stats_file):
            with open(log_stats_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                NOTIFICATION_LOG.update(loaded_data)
            log_notification_event("已載入通知統計數據")
    except Exception as e:
        log_notification_event(f"無法載入通知統計數據: {e}", 'warning')

def retry_failed_notifications():
    """重試之前失敗的通知"""
    log_file = os.path.join(LOG_DIR, 'failed_notifications.log')
    if not os.path.exists(log_file):
        return
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 清空原始日誌
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('')
        
        # 解析失敗通知
        sections = content.split('=' * 50)
        notifications = []
        
        for section in sections:
            if not section.strip():
                continue
            
            lines = section.strip().split('\n')
            if len(lines) < 3:
                continue
            
            try:
                # 解析主題和內容
                timestamp_line = lines[0].strip()
                subject_line = lines[1].strip()
                subject = subject_line.replace('主題: ', '', 1)
                
                # 收集剩餘行作為消息內容
                message_start = False
                message_lines = []
                for line in lines[2:]:
                    if line.startswith('內容:'):
                        message_start = True
                        continue
                    if message_start:
                        message_lines.append(line)
                
                message = '\n'.join(message_lines)
                notifications.append((subject, message))
            except Exception as e:
                log_notification_event(f"解析失敗通知格式錯誤: {e}", 'warning')
        
        # 重試發送
        success_count = 0
        for subject, message in notifications:
            try:
                if send_notification(message, subject):
                    success_count += 1
                else:
                    # 如果仍然失敗，重新記錄
                    log_notification_failure(message, subject)
            except Exception as e:
                log_notification_event(f"重試發送通知失敗: {e}", 'warning')
                log_notification_failure(message, subject)
        
        if success_count > 0:
            log_notification_event(f"成功重試發送 {success_count}/{len(notifications)} 條之前失敗的通知")
    except Exception as e:
        log_notification_event(f"重試失敗通知時發生錯誤: {e}", 'error')

# 初始化時載入之前的通知狀態
try:
    load_notification_log()
except Exception as e:
    print(f"[dual_notifier] 載入通知日誌時出錯: {e}")

# 嘗試重試之前失敗的通知
try:
    retry_failed_notifications()
except Exception as e:
    print(f"[dual_notifier] 重試失敗通知時出錯: {e}")

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
