"""
LINE 推播模組 - 整合 line_bot.py
"""
print("[line_bot] ✅ 已載入最新版")

import requests
import os

# 從環境變數獲取 LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")


def send_line_bot_message(message: str):
    """
    發送 LINE 訊息
    
    參數:
    - message: 要發送的訊息內容
    """
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("[line_bot] ❌ 缺少 LINE Token 或 User ID，無法推播")
        return

    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }

    try:
        response = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)
        if response.status_code != 200:
            print(f"[line_bot] ❌ 推播失敗：{response.status_code} - {response.text}")
        else:
            print("[line_bot] ✅ LINE 訊息推播成功")
    except Exception as e:
        print(f"[line_bot] ❌ 推播過程發生錯誤：{e}")


def send_stock_recommendation(user_id, stocks, time_slot):
    """
    發送股票推薦訊息
    
    參數:
    - user_id: LINE 用戶 ID
    - stocks: 推薦股票列表
    - time_slot: 時段名稱
    """
    if not stocks:
        message = f"【{time_slot}推薦股票】\n\n沒有符合條件的推薦股票"
        send_line_bot_message(message)
        return
    
    message = f"【{time_slot}推薦股票】\n\n"
    for stock in stocks:
        message += f"📈 {stock['code']} {stock['name']}\n"
        message += f"推薦理由: {stock['reason']}\n"
        message += f"目標價: {stock['target_price']}\n"
        message += f"止損價: {stock['stop_loss']}\n\n"
    
    send_line_bot_message(message)


def send_weak_valley_alerts(user_id, weak_valleys):
    """
    發送極弱谷警報訊息
    
    參數:
    - user_id: LINE 用戶 ID
    - weak_valleys: 極弱谷股票列表
    """
    if not weak_valleys:
        return
    
    message = "【極弱谷警報】\n\n"
    for stock in weak_valleys:
        message += f"⚠️ {stock['code']} {stock['name']}\n"
        message += f"當前價格: {stock['current_price']}\n"
        message += f"警報原因: {stock['alert_reason']}\n\n"
    
    send_line_bot_message(message)


def send_opening_report(recommended_stocks, watchlist_stocks, weak_stocks):
    """
    發送開盤前分析報告
    
    參數:
    - recommended_stocks: 推薦股票列表
    - watchlist_stocks: 觀察股票列表
    - weak_stocks: 走弱股票列表
    """
    from datetime import datetime
    
    now = datetime.now().strftime("%Y/%m/%d")
    message = f"📈 {now} 開盤推薦分析結果\n"

    if recommended_stocks:
        message += "\n✅ 推薦股：\n"
        for stock in recommended_stocks:
            message += f"🔹 {stock['stock_id']} {stock['name']}｜分數：{stock['score']}\n➡️ {stock['reason']}\n💡 建議：{stock['suggestion']}\n\n"
    else:
        message += "\n✅ 推薦股：無\n"

    if watchlist_stocks:
        message += "\n📌 觀察股（分數高但未達門檻）：\n"
        for stock in watchlist_stocks:
            message += f"🔸 {stock['stock_id']} {stock['name']}｜分數：{stock['score']}\n➡️ {stock['reason']}\n\n"

    if weak_stocks:
        message += "\n⚠️ 走弱警示股：\n"
        for stock in weak_stocks:
            message += f"❗ {stock['stock_id']} {stock['name']}｜走弱原因：{stock['reason']}\n"

    send_line_bot_message(message.strip())
