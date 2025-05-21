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
from datetime import datetime, timedelta

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
        'retry_count': int(os.getenv('EMAIL_RETRY_COUNT', '3')),
        'retry_delay': int(os.getenv('EMAIL_RETRY_DELAY', '5'))  # 秒
    },
    'line': {
        'token': os.getenv('LINE_CHANNEL_ACCESS_TOKEN'),
        'user_id': os.getenv('LINE_USER_ID'),
        'retry_count': int(os.getenv('LINE_RETRY_COUNT', '3')),
        'retry_delay': int(os.getenv('LINE_RETRY_DELAY', '5'))  # 秒
    },
    'backup': {
        'enabled': os.getenv('BACKUP_NOTIFICATIONS_ENABLED', 'true').lower() in ('true', 'yes', '1', 'on'),
        'retention_days': int(os.getenv('NOTIFICATION_BACKUP_RETENTION', '30')),
        'interval_minutes': int(os.getenv('NOTIFICATION_RETRY_INTERVAL', '60'))  # 失敗通知重試間隔(分鐘)
    }
}

# 通知紀錄和狀態追蹤
NOTIFICATION_LOG = {
    'last_email_success': None,
    'last_line_success': None,
    'last_retry_check': None,
    'email_stats': {
        'total_sent': 0,
        'successful': 0,
        'failed': 0
    },
    'line_stats': {
        'total_sent': 0,
        'successful': 0,
        'failed': 0
    },
    'failed_attempts': {
        'email': 0,
        'line': 0
    }
}

def send_notification(message, subject, html_body=None, retry=True, urgent=False):
    """
    發送通知(郵件和LINE)，增加錯誤處理和重試機制
    
    參數:
    - message: 通知文本內容
    - subject: 郵件主題
    - html_body: HTML格式的郵件正文(可選)
    - retry: 是否啟用重試機制
    - urgent: 是否為緊急通知（影響重試策略）
    
    返回:
    - bool: 通知是否成功發送
    """
    # 嘗試發送電子郵件
    email_success = send_email(message, subject, html_body, retry)
    
    # 嘗試發送LINE通知
    line_success = send_line_notify(message, retry)
    
    # 如果兩種方式都失敗，寫入本地日誌
    if not email_success and not line_success:
        log_notification_failure(message, subject, html_body, urgent)
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
    
    返回:
    - bool: 郵件是否成功發送
    """
    try:
        # 獲取郵件設置
        email_config = NOTIFICATION_CONFIG.get('email', {})
        smtp_server = email_config.get('smtp_server')
        smtp_port = email_config.get('smtp_port')
        smtp_user = email_config.get('user')
        smtp_password = email_config.get('password')
        email_to = email_config.get('to')
        
        # 更新發送統計
        NOTIFICATION_LOG['email_stats']['total_sent'] += 1
        
        if not all([smtp_server, smtp_port, smtp_user, smtp_password, email_to]):
            log_notification_event("郵件設置不完整，跳過發送", 'warning')
            NOTIFICATION_LOG['email_stats']['failed'] += 1
            save_notification_log()
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
        msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0800")
        
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
                NOTIFICATION_LOG['email_stats']['successful'] += 1
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
                    NOTIFICATION_LOG['email_stats']['failed'] += 1
                    save_notification_log()
                    
                    # 嘗試不同的SMTP連接方式
                    backup_result = try_alternative_smtp(msg, smtp_user, smtp_password, email_to)
                    if backup_result:
                        NOTIFICATION_LOG['email_stats']['successful'] += 1
                        NOTIFICATION_LOG['email_stats']['failed'] -= 1  # 修正失敗計數
                        save_notification_log()
                    
                    return backup_result
        
    except Exception as e:
        log_notification_event(f"郵件發送發生異常: {e}", 'error')
        log_notification_event(traceback.format_exc(), 'error')
        NOTIFICATION_LOG['failed_attempts']['email'] += 1
        NOTIFICATION_LOG['email_stats']['failed'] += 1
        save_notification_log()
        return False

def try_alternative_smtp(msg, smtp_user, smtp_password, email_to):
    """嘗試使用不同的SMTP設定發送郵件"""
    try:
        # 嘗試使用其他常見的SMTP設定
        log_notification_event("嘗試使用不同的SMTP設定...")
        
        if not all([smtp_user, smtp_password, email_to]):
            return False

        # Gmail 的備用端口
        alternate_settings = [
            ("smtp.gmail.com", 465, True),   # SSL
            ("smtp.gmail.com", 587, False),  # TLS
            ("smtp.gmail.com", 25, False),   # 基本
            ("smtp-mail.outlook.com", 587, False),  # Outlook
            ("smtp.mail.yahoo.com", 587, False)     # Yahoo
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
                        
                log_notification_event(f"備用郵件伺服器發送成功")
                NOTIFICATION_LOG['last_email_success'] = datetime.now().isoformat()
                NOTIFICATION_LOG['failed_attempts']['email'] = 0
                save_notification_log()
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
    
    返回:
    - bool: 通知是否成功發送
    """
    try:
        # 獲取LINE設置
        line_config = NOTIFICATION_CONFIG.get('line', {})
        token = line_config.get('token')
        
        # 更新發送統計
        NOTIFICATION_LOG['line_stats']['total_sent'] += 1
        
        if not token:
            log_notification_event("LINE設置不完整，跳過發送", 'warning')
            NOTIFICATION_LOG['line_stats']['failed'] += 1
            save_notification_log()
            return False
        
        # 消息長度檢查和分割
        max_message_length = 1000  # LINE Notify的消息長度限制
        messages = []
        
        if len(message) > max_message_length:
            # 分割消息
            chunks = [message[i:i+max_message_length] for i in range(0, len(message), max_message_length)]
            
            for i, chunk in enumerate(chunks):
                if i == 0:
                    messages.append(chunk)
                else:
                    messages.append(f"(續) {chunk}")
        else:
            messages = [message]
        
        # 增加重試邏輯
        max_retries = line_config.get('retry_count', 3) if retry else 1
        retry_delay = line_config.get('retry_delay', 5)  # 秒
        
        all_success = True
        
        for msg_part in messages:
            success = False
            
            for attempt in range(max_retries):
                try:
                    # 發送LINE通知
                    url = 'https://notify-api.line.me/api/notify'
                    headers = {'Authorization': f'Bearer {token}'}
                    data = {'message': msg_part}
                    
                    response = requests.post(url, headers=headers, data=data, timeout=30)
                    
                    if response.status_code == 200:
                        success = True
                        break
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
            
            all_success = all_success and success
            
            # 分段消息之間添加延遲，避免速率限制
            if len(messages) > 1 and msg_part != messages[-1]:
                time.sleep(1)
        
        if all_success:
            log_notification_event("LINE通知發送成功")
            NOTIFICATION_LOG['last_line_success'] = datetime.now().isoformat()
            NOTIFICATION_LOG['failed_attempts']['line'] = 0
            NOTIFICATION_LOG['line_stats']['successful'] += 1
        else:
            NOTIFICATION_LOG['line_stats']['failed'] += 1
            
        save_notification_log()
        return all_success
                    
    except Exception as e:
        log_notification_event(f"LINE通知發送發生異常: {e}", 'error')
        log_notification_event(traceback.format_exc(), 'error')
        NOTIFICATION_LOG['failed_attempts']['line'] += 1
        NOTIFICATION_LOG['line_stats']['failed'] += 1
        save_notification_log()
        return False

def log_notification_failure(message, subject, html_body=None, urgent=False):
    """記錄發送失敗的通知到本地文件，以便後續重試"""
    try:
        failed_dir = os.path.join(LOG_DIR, 'failed_notifications')
        os.makedirs(failed_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"failed_{timestamp}{'_urgent' if urgent else ''}.json"
        failed_file = os.path.join(failed_dir, filename)
        
        failed_data = {
            'timestamp': datetime.now().isoformat(),
            'subject': subject,
            'message': message,
            'html_body': html_body,
            'urgent': urgent,
            'retry_count': 0,
            'last_retry': None
        }
        
        with open(failed_file, 'w', encoding='utf-8') as f:
            json.dump(failed_data, f, ensure_ascii=False, indent=2)
            
        log_notification_event(f"通知失敗，已記錄到 {failed_file}")
        
        # 同時保存到綜合日誌
        log_file = os.path.join(LOG_DIR, 'failed_notifications.log')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"===== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====\n")
            f.write(f"主題: {subject}\n")
            f.write(f"緊急: {'是' if urgent else '否'}\n")
            f.write(f"內容:\n{message}\n")
            f.write("="*50 + "\n\n")
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
        
        # 添加上次保存時間
        NOTIFICATION_LOG['last_updated'] = datetime.now().isoformat()
        
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
                for key, value in loaded_data.items():
                    NOTIFICATION_LOG[key] = value
            log_notification_event("已載入通知統計數據")
    except Exception as e:
        log_notification_event(f"無法載入通知統計數據: {e}", 'warning')

def retry_failed_notifications(max_retries=None, only_urgent=False):
    """
    重試之前失敗的通知
    
    參數:
    - max_retries: 最大重試次數，None表示不限制
    - only_urgent: 是否只重試緊急通知
    
    返回:
    - 元組: (重試次數, 成功次數)
    """
    failed_dir = os.path.join(LOG_DIR, 'failed_notifications')
    if not os.path.exists(failed_dir):
        return 0, 0
    
    # 更新上次檢查時間
    NOTIFICATION_LOG['last_retry_check'] = datetime.now().isoformat()
    save_notification_log()
    
    # 重試間隔時間
    retry_interval_minutes = NOTIFICATION_CONFIG.get('backup', {}).get('interval_minutes', 60)
    min_retry_age = datetime.now() - timedelta(minutes=retry_interval_minutes)
    
    # 獲取失敗通知文件列表
    failed_files = []
    for filename in os.listdir(failed_dir):
        if filename.startswith('failed_') and filename.endswith('.json'):
            failed_files.append(os.path.join(failed_dir, filename))
    
    if not failed_files:
        return 0, 0
    
    retry_count = 0
    success_count = 0
    
    for file_path in failed_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                notification_data = json.load(f)
            
            # 檢查是否符合條件進行重試
            if only_urgent and not notification_data.get('urgent', False):
                continue
                
            # 檢查重試次數限制
            current_retries = notification_data.get('retry_count', 0)
            if max_retries is not None and current_retries >= max_retries:
                continue
                
            # 檢查上次重試時間，避免頻繁重試
            last_retry_str = notification_data.get('last_retry')
            if last_retry_str:
                last_retry = datetime.fromisoformat(last_retry_str)
                if last_retry > min_retry_age:
                    continue
            
            # 執行重試
            subject = notification_data.get('subject', '重試通知')
            message = notification_data.get('message', '')
            html_body = notification_data.get('html_body')
            
            log_notification_event(f"重試發送通知：{subject}（第 {current_retries + 1} 次）")
            
            # 嘗試發送
            success = send_notification(message, subject, html_body, retry=True, urgent=notification_data.get('urgent', False))
            retry_count += 1
            
            if success:
                # 發送成功，刪除失敗記錄
                os.remove(file_path)
                success_count += 1
                log_notification_event(f"重試成功，已刪除失敗記錄: {os.path.basename(file_path)}")
            else:
                # 發送失敗，更新重試計數
                notification_data['retry_count'] = current_retries + 1
                notification_data['last_retry'] = datetime.now().isoformat()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(notification_data, f, ensure_ascii=False, indent=2)
                
                log_notification_event(f"重試失敗，已更新重試計數: {os.path.basename(file_path)}", 'warning')
        except Exception as e:
            log_notification_event(f"處理失敗通知文件出錯: {e}", 'error')
    
    return retry_count, success_count

def cleanup_old_failed_notifications():
    """
    清理舊的失敗通知記錄
    
    返回:
    - 已清理的文件數量
    """
    failed_dir = os.path.join(LOG_DIR, 'failed_notifications')
    if not os.path.exists(failed_dir):
        return 0
    
    # 獲取保留天數設置
    retention_days = NOTIFICATION_CONFIG.get('backup', {}).get('retention_days', 30)
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    # 統計已清理的文件數量
    cleaned_count = 0
    
    for filename in os.listdir(failed_dir):
        if not filename.startswith('failed_') or not filename.endswith('.json'):
            continue
            
        file_path = os.path.join(failed_dir, filename)
        
        try:
            # 檢查文件修改時間
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            if file_time < cutoff_date:
                # 檢查文件內容中的時間戳
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    timestamp = data.get('timestamp')
                    if timestamp:
                        file_date = datetime.fromisoformat(timestamp)
                        if file_date > cutoff_date:
                            # 文件時間超過但內容時間還沒有，保留文件
                            continue
                except:
                    # 讀取文件內容失敗，基於文件時間判斷
                    pass
                
                # 刪除文件
                os.remove(file_path)
                log_notification_event(f"清理過期的失敗通知記錄: {filename}")
                cleaned_count += 1
                
        except Exception as e:
            log_notification_event(f"處理文件 {filename} 時出錯: {e}", 'warning')
    
    return cleaned_count

def get_notification_stats():
    """
    獲取通知系統統計數據
    
    返回:
    - dict: 通知統計數據
    """
    # 獲取失敗通知數量
    failed_dir = os.path.join(LOG_DIR, 'failed_notifications')
    failed_count = 0
    if os.path.exists(failed_dir):
        failed_count = len([f for f in os.listdir(failed_dir) if f.startswith('failed_') and f.endswith('.json')])
    
    # 計算成功率
    email_success_rate = 0
    if NOTIFICATION_LOG['email_stats']['total_sent'] > 0:
        email_success_rate = round(NOTIFICATION_LOG['email_stats']['successful'] / NOTIFICATION_LOG['email_stats']['total_sent'] * 100, 2)
    
    line_success_rate = 0
    if NOTIFICATION_LOG['line_stats']['total_sent'] > 0:
        line_success_rate = round(NOTIFICATION_LOG['line_stats']['successful'] / NOTIFICATION_LOG['line_stats']['total_sent'] * 100, 2)
    
    return {
        'email': {
            'total_sent': NOTIFICATION_LOG['email_stats']['total_sent'],
            'successful': NOTIFICATION_LOG['email_stats']['successful'],
            'failed': NOTIFICATION_LOG['email_stats']['failed'],
            'success_rate': email_success_rate,
            'last_success': NOTIFICATION_LOG['last_email_success']
        },
        'line': {
            'total_sent': NOTIFICATION_LOG['line_stats']['total_sent'],
            'successful': NOTIFICATION_LOG['line_stats']['successful'],
            'failed': NOTIFICATION_LOG['line_stats']['failed'],
            'success_rate': line_success_rate,
            'last_success': NOTIFICATION_LOG['last_line_success']
        },
        'failed_notifications': {
            'pending': failed_count,
            'last_retry_check': NOTIFICATION_LOG['last_retry_check']
        },
        'last_updated': datetime.now().isoformat()
    }

# 初始化時載入之前的通知狀態
try:
    load_notification_log()
except Exception as e:
    print(f"[dual_notifier] 載入通知日誌時出錯: {e}")

# 嘗試重試之前失敗的通知 - 只在加載模組時嘗試緊急通知
try:
    # 先嘗試緊急通知
    retry_count, success_count = retry_failed_notifications(max_retries=None, only_urgent=True)
    if retry_count > 0:
        log_notification_event(f"啟動時重試了 {retry_count} 條緊急通知，成功 {success_count} 條")
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
