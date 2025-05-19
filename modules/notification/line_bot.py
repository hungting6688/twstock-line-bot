"""
修復版 LINE Bot 模組 - 增強錯誤處理和重試機制
"""
print("[line_bot] ✅ 已載入最新版")

import requests
import os
import time
import random

# 從環境變數獲取 LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")


def send_line_bot_message(message: str, max_retries=2):
    """
    發送 LINE 訊息，增強錯誤處理和重試機制
    
    參數:
    - message: 要發送的訊息內容
    - max_retries: 最大重試次數
    
    返回:
    - bool: 是否成功發送
    
    拋出:
    - Exception: 發送失敗時拋出例外，包含詳細錯誤訊息
    """
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        error_msg = "[line_bot] ❌ 缺少 LINE Token 或 User ID，無法推播"
        print(error_msg)
        raise Exception(error_msg)

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

    # 重試機制
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                "https://api.line.me/v2/bot/message/push", 
                headers=headers, 
                json=payload, 
                timeout=30
            )
            
            if response.status_code == 200:
                print("[line_bot] ✅ LINE 訊息推播成功")
                return True
            
            # 處理特定錯誤碼
            if response.status_code == 429:  # Too Many Requests 錯誤
                error_msg = f"[line_bot] ❌ 推播失敗：429 - 達到速率限制或月度配額"
                print(error_msg)
                # 如果已達到最大重試次數，則拋出異常
                if attempt >= max_retries:
                    raise Exception(error_msg + f" - 內容: {response.text}")
                # 等待較長時間後重試
                wait_time = 5 * (attempt + 1)
                print(f"[line_bot] ⏳ 等待 {wait_time} 秒後重試 ({attempt+1}/{max_retries})...")
                time.sleep(wait_time)
                continue
            
            # 其他錯誤
            error_msg = f"[line_bot] ❌ 推播失敗：{response.status_code} - {response.text}"
            print(error_msg)
            
            # 如果已達到最大重試次數，則拋出異常
            if attempt >= max_retries:
                raise Exception(error_msg)
            
            # 等待一段時間後重試
            wait_time = 2 * (attempt + 1) + random.uniform(0, 1)
            print(f"[line_bot] ⏳ 等待 {wait_time:.1f} 秒後重試 ({attempt+1}/{max_retries})...")
            time.sleep(wait_time)
            
        except requests.exceptions.RequestException as e:
            # 網絡錯誤處理
            error_msg = f"[line_bot] ❌ 推播過程發生網絡錯誤：{e}"
            print(error_msg)
            
            # 如果已達到最大重試次數，則拋出異常
            if attempt >= max_retries:
                raise Exception(error_msg)
            
            # 等待一段時間後重試
            wait_time = 2 * (attempt + 1) + random.uniform(0, 1)
            print(f"[line_bot] ⏳ 等待 {wait_time:.1f} 秒後重試 ({attempt+1}/{max_retries})...")
            time.sleep(wait_time)
    
    # 如果所有重試都失敗
    raise Exception("[line_bot] ❌ 所有重試嘗試均失敗")


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

    # 檢查訊息長度，LINE 單則訊息有5000字元的限制
    if len(message) > 4500:
        # 分割訊息
        parts = []
        current_part = message[:4500]
        parts.append(current_part)
        
        if recommended_stocks and watchlist_stocks:
            part2 = f"📈 {now} 開盤推薦分析結果 (續)\n\n"
            if weak_stocks:
                part2 += "\n⚠️ 走弱警示股：\n"
                for stock in weak_stocks:
                    part2 += f"❗ {stock['stock_id']} {stock['name']}｜走弱原因：{stock['reason']}\n"
            parts.append(part2)
        
        # 分別發送每一部分
        for i, part in enumerate(parts):
            try:
                send_line_bot_message(part)
                # 避免訊息被視為洪水攻擊
                if i < len(parts) - 1:
                    time.sleep(1)
            except Exception as e:
                print(f"[line_bot] ❌ 發送訊息第 {i+1} 部分失敗: {e}")
    else:
        send_line_bot_message(message.strip())

# 測試函數
if __name__ == "__main__":
    test_message = "這是一條測試訊息，用於確認 LINE Bot 推播功能是否正常。"
    try:
        send_line_bot_message(test_message)
        print("LINE 測試訊息發送成功！")
    except Exception as e:
        print(f"LINE 測試訊息發送失敗: {e}")
