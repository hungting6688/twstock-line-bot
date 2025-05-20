"""
改進的 LINE Bot 模組 - 增強穩定性和錯誤處理
"""
print("[line_bot] ✅ 已載入最新版")

import requests
import os
import time
import random
import json

# 從環境變數獲取 LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# 嘗試讀取已知的最近發送錯誤狀態
try:
    LINE_ERROR_STATE_FILE = os.path.join(os.path.dirname(__file__), '../../cache/line_error_state.json')
    os.makedirs(os.path.dirname(LINE_ERROR_STATE_FILE), exist_ok=True)
    if os.path.exists(LINE_ERROR_STATE_FILE):
        with open(LINE_ERROR_STATE_FILE, 'r') as f:
            line_error_state = json.load(f)
    else:
        line_error_state = {
            "last_error": None,
            "error_count": 0,
            "last_error_time": None
        }
except:
    line_error_state = {
        "last_error": None,
        "error_count": 0,
        "last_error_time": None
    }

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
    global line_error_state
    
    # 檢查環境變數
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        error_msg = "[line_bot] ❌ 缺少 LINE Token 或 User ID，無法推播"
        print(error_msg)
        
        # 記錄錯誤
        line_error_state["last_error"] = "MISSING_CREDENTIALS"
        line_error_state["error_count"] += 1
        line_error_state["last_error_time"] = time.time()
        try:
            with open(LINE_ERROR_STATE_FILE, 'w') as f:
                json.dump(line_error_state, f)
        except:
            pass
            
        raise Exception(error_msg)

    # 檢查訊息長度，如果超過 LINE 的限制（5000 字元），進行截斷
    if len(message) > 4900:  # 留一些緩衝區
        original_message = message
        message = message[:4800] + "\n...\n(訊息已截斷，詳情請查看電子郵件)"
        print(f"[line_bot] ⚠️ 訊息過長({len(original_message)}字元)，已截斷至 4800 字元")

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
                timeout=30  # 增加超時時間
            )
            
            response_body = response.text
            
            if response.status_code == 200:
                print("[line_bot] ✅ LINE 訊息推播成功")
                
                # 重置錯誤計數器
                line_error_state["last_error"] = None
                line_error_state["error_count"] = 0
                line_error_state["last_error_time"] = None
                try:
                    with open(LINE_ERROR_STATE_FILE, 'w') as f:
                        json.dump(line_error_state, f)
                except:
                    pass
                    
                return True
            
            # 處理特定錯誤碼
            if response.status_code == 429:  # Too Many Requests 錯誤
                error_msg = f"[line_bot] ❌ 推播失敗：429 - 達到速率限制或月度配額"
                print(error_msg)
                
                # 記錄錯誤
                line_error_state["last_error"] = "RATE_LIMIT"
                line_error_state["error_count"] += 1
                line_error_state["last_error_time"] = time.time()
                try:
                    with open(LINE_ERROR_STATE_FILE, 'w') as f:
                        json.dump(line_error_state, f)
                except:
                    pass
                
                # 如果已達到最大重試次數，則拋出異常
                if attempt >= max_retries:
                    full_error = f"{error_msg} - 內容: {response_body}"
                    raise Exception(full_error)
                
                # 等待較長時間後重試
                wait_time = 5 * (attempt + 1)
                print(f"[line_bot] ⏳ 等待 {wait_time} 秒後重試 ({attempt+1}/{max_retries})...")
                time.sleep(wait_time)
                continue
            
            # 其他錯誤
            error_msg = f"[line_bot] ❌ 推播失敗：{response.status_code} - {response_body}"
            print(error_msg)
            
            # 記錄錯誤
            line_error_state["last_error"] = f"HTTP_{response.status_code}"
            line_error_state["error_count"] += 1
            line_error_state["last_error_time"] = time.time()
            try:
                with open(LINE_ERROR_STATE_FILE, 'w') as f:
                    json.dump(line_error_state, f)
            except:
                pass
            
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
            
            # 記錄錯誤
            line_error_state["last_error"] = "NETWORK_ERROR"
            line_error_state["error_count"] += 1
            line_error_state["last_error_time"] = time.time()
            try:
                with open(LINE_ERROR_STATE_FILE, 'w') as f:
                    json.dump(line_error_state, f)
            except:
                pass
            
            # 如果已達到最大重試次數，則拋出異常
            if attempt >= max_retries:
                raise Exception(error_msg)
            
            # 等待一段時間後重試
            wait_time = 2 * (attempt + 1) + random.uniform(0, 1)
            print(f"[line_bot] ⏳ 等待 {wait_time:.1f} 秒後重試 ({attempt+1}/{max_retries})...")
            time.sleep(wait_time)
    
    # 如果所有重試都失敗
    raise Exception("[line_bot] ❌ 所有重試嘗試均失敗")


def check_line_service_status():
    """
    檢查 LINE Bot 服務狀態
    
    返回:
    - dict: 服務狀態信息
    """
    global line_error_state
    
    # 檢查是否有可用的憑據
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        return {
            "status": "unavailable",
            "reason": "missing_credentials",
            "message": "缺少 LINE Bot 認證資訊"
        }
    
    # 檢查最近錯誤狀態
    if line_error_state["last_error"] == "RATE_LIMIT" and line_error_state["last_error_time"]:
        # 檢查是否在1小時內發生過速率限制錯誤
        if time.time() - line_error_state["last_error_time"] < 3600:
            return {
                "status": "limited",
                "reason": "rate_limit",
                "message": "LINE Bot 正在速率限制中",
                "error_count": line_error_state["error_count"]
            }
    
    # 檢查服務狀態 - 發送一個簡單的 GET 請求檢查 API 是否可用
    try:
        headers = {
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
        }
        
        response = requests.get(
            "https://api.line.me/v2/bot/info", 
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                "status": "available",
                "message": "LINE Bot 服務正常"
            }
        else:
            return {
                "status": "error",
                "reason": f"http_{response.status_code}",
                "message": f"LINE Bot API 返回錯誤: {response.status_code}",
                "details": response.text
            }
    except Exception as e:
        return {
            "status": "error",
            "reason": "connection_error",
            "message": f"LINE Bot 連接錯誤: {str(e)}"
        }

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
    
    message += "註：極弱谷表示股票處於超賣狀態，可以觀察反彈機會，但要注意風險控制。"
    
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
