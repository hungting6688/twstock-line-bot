"""
電子郵件通知模組 - 作為 LINE 通知的備份方案
"""
print("[email_notifier] ✅ 已載入電子郵件通知模組")

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from email.utils import formatdate

# 從環境變數獲取電子郵件設定
EMAIL_SENDER = os.getenv("EMAIL_SENDER")        # 發件人郵箱
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")    # 發件人密碼或應用密碼
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")    # 收件人郵箱
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")  # SMTP 服務器
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))            # SMTP 端口

def send_email(subject, body, html_body=None):
    """
    發送電子郵件
    
    參數:
    - subject: 郵件主題
    - body: 郵件正文 (純文本)
    - html_body: 郵件正文 (HTML格式，可選)
    
    返回:
    - bool: 是否成功發送
    """
    if not EMAIL_SENDER or not EMAIL_PASSWORD or not EMAIL_RECEIVER:
        print("[email_notifier] ❌ 缺少電子郵件設定，無法發送郵件")
        print("[email_notifier] 提示: 請設置 EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER 環境變數")
        return False
    
    # 創建郵件
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Date"] = formatdate(localtime=True)
    
    # 添加純文本正文
    msg.attach(MIMEText(body, "plain", "utf-8"))
    
    # 添加 HTML 正文 (如果提供)
    if html_body:
        msg.attach(MIMEText(html_body, "html", "utf-8"))
    
    try:
        # 連接到 SMTP 服務器
        server = smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
        server.starttls()  # 啟用 TLS 加密
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        
        # 發送郵件
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        server.quit()
        
        print("[email_notifier] ✅ 電子郵件發送成功")
        return True
    except Exception as e:
        print(f"[email_notifier] ❌ 電子郵件發送失敗: {e}")
        return False

def send_stock_recommendation_email(stocks, time_slot):
    """
    發送股票推薦電子郵件
    
    參數:
    - stocks: 推薦股票列表
    - time_slot: 時段名稱
    """
    if not stocks:
        subject = f"【{time_slot}推薦股票】- 無推薦"
        body = f"【{time_slot}推薦股票】\n\n沒有符合條件的推薦股票"
        send_email(subject, body)
        return
    
    subject = f"【{time_slot}推薦股票】- {len(stocks)} 檔股票"
    
    # 純文本版本
    body = f"【{time_slot}推薦股票】\n\n"
    for stock in stocks:
        body += f"📈 {stock['code']} {stock['name']}\n"
        body += f"推薦理由: {stock['reason']}\n"
        body += f"目標價: {stock['target_price']}\n"
        body += f"止損價: {stock['stop_loss']}\n\n"
    
    # HTML 版本 (更漂亮的格式)
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
        <div class="header">【{time_slot}推薦股票】</div>
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
    
    send_email(subject, body, html_body)

def send_weak_valley_alerts_email(weak_valleys):
    """
    發送極弱谷警報電子郵件
    
    參數:
    - weak_valleys: 極弱谷股票列表
    """
    if not weak_valleys:
        return
    
    subject = f"【極弱谷警報】- {len(weak_valleys)} 檔股票"
    
    # 純文本版本
    body = "【極弱谷警報】\n\n"
    for stock in weak_valleys:
        body += f"⚠️ {stock['code']} {stock['name']}\n"
        body += f"當前價格: {stock['current_price']}\n"
        body += f"警報原因: {stock['alert_reason']}\n\n"
    
    # HTML 版本
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
    
    send_email(subject, body, html_body)

# 測試電子郵件功能
if __name__ == "__main__":
    print("測試電子郵件發送功能")
    test_subject = "台股分析系統 - 郵件通知測試"
    test_body = "這是一封測試郵件，用於確認台股分析系統的郵件通知功能是否正常運作。"
    send_email(test_subject, test_body)
