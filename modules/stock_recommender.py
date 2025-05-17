print("[stock_recommender] ✅ 已載入最新版")

import twstock
import pandas as pd
import numpy as np
from datetime import datetime
from modules.multi_analysis import analyze_stock_value
from modules.line_bot import send_line_bot_message

def get_stock_recommendations(time_slot, count=5):
    """
    根據時段獲取推薦股票
    
    參數:
    - time_slot: 時段 ('morning', 'noon', 'afternoon', 'evening')
    - count: 推薦股票數量
    
    返回:
    - 推薦股票列表
    """
    print(f"[stock_recommender] ⏳ 執行{time_slot}推薦分析...")
    
    # 根據不同時段使用不同策略
    if time_slot == 'morning':
        # 早盤策略: 基於昨日收盤和技術指標選股
        return morning_strategy(count)
    elif time_slot == 'noon':
        # 中午策略: 基於上午交易數據和量能選股
        return noon_strategy(count)
    elif time_slot == 'afternoon':
        # 下午策略: 基於早盤趨勢和突破選股
        return afternoon_strategy(count)
    elif time_slot == 'evening':
        # 收盤後策略: 基於全日數據和明日展望選股
        return evening_strategy(count)
    else:
        return []

def morning_strategy(count):
    """早盤前推薦策略"""
    # 取得台股所有上市公司代碼
    from modules.twse_scraper import get_all_valid_twse_stocks
    all_stocks = get_all_valid_twse_stocks()
    
    print("[stock_recommender] 分析技術指標與基本面...")
    
    # 選擇權重較高的股票
    candidates = []
    for stock_info in all_stocks[:300]:  # 限制分析數量，避免過度耗時
        code = stock_info['stock_id']
        name = stock_info['stock_name']
            
        # 使用多重分析進行評分
        score, analysis = analyze_stock_value(code)
        if score > 80:  # 高分股票作為候選
            candidates.append({
                'code': code,
                'name': name,
                'score': score,
                'analysis': analysis
            })
    
    # 根據分數排序並選出前N名
    candidates.sort(key=lambda x: x['score'], reverse=True)
    top_candidates = candidates[:count]
    
    # 為每個推薦股票添加詳細資訊
    recommendations = []
    for candidate in top_candidates:
        try:
            # 使用 yfinance 獲取價格資訊，而不是 twstock
            import yfinance as yf
            ticker = yf.Ticker(f"{candidate['code']}.TW")
            history = ticker.history(period="1mo")
            
            if not history.empty:
                current_price = history['Close'].iloc[-1]
                ma_5 = history['Close'].tail(5).mean()
                ma_10 = history['Close'].tail(10).mean()
                
                target_price = round(current_price * 1.05, 2)  # 假設目標漲幅5%
                stop_loss = round(current_price * 0.97, 2)    # 假設止損點3%
                
                reason = f"技術面：{candidate['analysis'].get('technical', '無技術分析')}，"
                reason += f"基本面：{candidate['analysis'].get('fundamental', '無基本面分析')}"
                
                recommendations.append({
                    'code': candidate['code'],
                    'name': candidate['name'],
                    'reason': reason,
                    'target_price': target_price,
                    'stop_loss': stop_loss,
                    'current_price': current_price
                })
        except Exception as e:
            print(f"[stock_recommender] ⚠️ {candidate['code']} 處理失敗：{e}")
    
    return recommendations

def noon_strategy(count):
    """中午休盤策略"""
    from modules.ta_analysis import analyze_technical_indicators
    from modules.price_fetcher import get_top_stocks
    
    # 獲取前 100 檔熱門股
    stock_ids = get_top_stocks(limit=100)
    
    # 進行技術分析
    tech_results = analyze_technical_indicators(stock_ids)
    
    # 根據評分排序
    sorted_results = sorted([
        (sid, data) for sid, data in tech_results.items()
    ], key=lambda x: x[1]['score'], reverse=True)
    
    recommendations = []
    for sid, data in sorted_results[:count]:
        try:
            # 從 Yahoo Finance 獲取股票名稱
            import yfinance as yf
            ticker = yf.Ticker(f"{sid}.TW")
            info = ticker.info
            name = info.get('shortName', sid)
            
            current_price = ticker.history(period="1d")['Close'].iloc[-1]
            target_price = round(current_price * 1.03, 2)  # 短線目標 3%
            stop_loss = round(current_price * 0.98, 2)     # 止損點 2%
            
            recommendations.append({
                'code': sid,
                'name': name,
                'reason': data['desc'],
                'target_price': target_price,
                'stop_loss': stop_loss,
                'current_price': current_price
            })
        except Exception as e:
            print(f"[stock_recommender] ⚠️ {sid} 處理失敗：{e}")
    
    return recommendations

def afternoon_strategy(count):
    """尾盤前推薦策略"""
    # 使用與 noon_strategy 類似的邏輯，但增加盤中突破條件
    from modules.ta_analysis import analyze_technical_indicators
    from modules.price_fetcher import get_top_stocks
    
    # 獲取成交量較大的股票
    stock_ids = get_top_stocks(limit=150)
    
    # 進行技術分析
    tech_results = analyze_technical_indicators(stock_ids)
    
    # 篩選出盤中有突破趨勢的股票
    breakout_candidates = []
    for sid, data in tech_results.items():
        if data['score'] >= 5 and "均線" in data['desc'] and "KD" in data['desc']:
            # 檢查是否有量能配合
            try:
                import yfinance as yf
                ticker = yf.Ticker(f"{sid}.TW")
                history = ticker.history(period="5d")
                
                # 檢查今日成交量是否高於 5 日均量
                today_volume = history['Volume'].iloc[-1]
                avg_volume = history['Volume'].mean()
                
                if today_volume > avg_volume * 1.2:  # 成交量放大 20%
                    current_price = history['Close'].iloc[-1]
                    name = ticker.info.get('shortName', sid)
                    
                    breakout_candidates.append({
                        'code': sid,
                        'name': name,
                        'score': data['score'],
                        'desc': data['desc'],
                        'current_price': current_price
                    })
            except Exception as e:
                print(f"[stock_recommender] ⚠️ {sid} 量能檢查失敗：{e}")
    
    # 根據分數排序
    breakout_candidates.sort(key=lambda x: x['score'], reverse=True)
    
    # 取前 N 名
    recommendations = []
    for candidate in breakout_candidates[:count]:
        target_price = round(candidate['current_price'] * 1.02, 2)  # 短線目標 2%
        stop_loss = round(candidate['current_price'] * 0.985, 2)    # 止損點 1.5%
        
        recommendations.append({
            'code': candidate['code'],
            'name': candidate['name'],
            'reason': f"尾盤突破：{candidate['desc']}，搭配放量",
            'target_price': target_price,
            'stop_loss': stop_loss,
            'current_price': candidate['current_price']
        })
    
    return recommendations

def evening_strategy(count):
    """盤後分析推薦策略"""
    # 結合基本面和技術面，選出明日觀察標的
    from modules.ta_analysis import analyze_technical_indicators
    from modules.price_fetcher import get_top_stocks
    from modules.eps_dividend_scraper import get_eps_data
    
    # 獲取潛力股清單
    stock_ids = get_top_stocks(limit=200)
    
    # 進行技術分析
    tech_results = analyze_technical_indicators(stock_ids)
    
    # 獲取 EPS 資料
    eps_data = get_eps_data()
    
    # 綜合評分
    candidates = []
    for sid, data in tech_results.items():
        if data['score'] >= 5:
            try:
                import yfinance as yf
                ticker = yf.Ticker(f"{sid}.TW")
                info = ticker.info
                history = ticker.history(period="1mo")
                
                if history.empty:
                    continue
                
                name = info.get('shortName', sid)
                current_price = history['Close'].iloc[-1]
                
                # 基本面加分
                eps_info = eps_data.get(sid, {})
                eps = eps_info.get('eps', 0)
                dividend = eps_info.get('dividend', 0)
                
                # 計算綜合分數
                total_score = data['score']
                if eps > 5:
                    total_score += 2
                elif eps > 2:
                    total_score += 1
                
                if dividend > 4:
                    total_score += 2
                elif dividend > 2:
                    total_score += 1
                
                candidates.append({
                    'code': sid,
                    'name': name,
                    'tech_desc': data['desc'],
                    'eps': eps,
                    'dividend': dividend,
                    'total_score': total_score,
                    'current_price': current_price
                })
            except Exception as e:
                print(f"[stock_recommender] ⚠️ {sid} 綜合分析失敗：{e}")
    
    # 根據綜合分數排序
    candidates.sort(key=lambda x: x['total_score'], reverse=True)
    
    # 取前 N 名
    recommendations = []
    for candidate in candidates[:count]:
        eps_text = f"，EPS: {candidate['eps']}" if candidate['eps'] else ""
        div_text = f"，股息: {candidate['dividend']}%" if candidate['dividend'] else ""
        
        target_price = round(candidate['current_price'] * 1.05, 2)
        stop_loss = round(candidate['current_price'] * 0.97, 2)
        
        recommendations.append({
            'code': candidate['code'],
            'name': candidate['name'],
            'reason': f"明日關注：{candidate['tech_desc']}{eps_text}{div_text}",
            'target_price': target_price,
            'stop_loss': stop_loss,
            'current_price': candidate['current_price']
        })
    
    return recommendations

def get_weak_valley_alerts():
    """
    識別處於極弱谷狀態的股票
    
    返回:
    - 極弱谷股票列表
    """
    print("[stock_recommender] ⏳ 掃描極弱谷股票...")
    
    from modules.price_fetcher import get_top_stocks
    
    # 獲取成交量較大的股票
    stock_ids = get_top_stocks(limit=300)
    alerts = []
    
    for stock_id in stock_ids:
        try:
            import yfinance as yf
            ticker = yf.Ticker(f"{stock_id}.TW")
            history = ticker.history(period="60d")
            
            if history.empty or len(history) < 20:
                continue
            
            # 計算各項技術指標
            closes = history['Close'].values
            volumes = history['Volume'].values
            
            # 1. 計算 RSI
            delta = np.diff(closes)
            up = np.sum([d if d > 0 else 0 for d in delta[-14:]])
            down = np.sum([abs(d) if d < 0 else 0 for d in delta[-14:]])
            if down == 0:
                rsi = 100
            else:
                rs = up / down
                rsi = 100 - (100 / (1 + rs))
            
            # 2. 計算均線
            ma_5 = np.mean(closes[-5:])
            ma_10 = np.mean(closes[-10:])
            ma_20 = np.mean(closes[-20:])
            
            # 3. 檢查股價連續下跌天數
            days_falling = 0
            for i in range(len(closes)-1, 0, -1):
                if closes[i] < closes[i-1]:
                    days_falling += 1
                else:
                    break
            
            # 判斷極弱谷條件
            is_weak_valley = False
            reason = []
            
            # RSI 超賣
            if rsi < 30:
                is_weak_valley = True
                reason.append(f"RSI={rsi:.1f}處於超賣區間")
            
            # 跌破均線
            if closes[-1] < ma_20 * 0.95:
                is_weak_valley = True
                reason.append("股價跌破20日均線5%以上")
            
            # 連續下跌
            if days_falling >= 4:
                is_weak_valley = True
                reason.append(f"連續下跌{days_falling}天")
            
            # 綜合判斷
            if is_weak_valley and len(reason) >= 2:  # 至少滿足兩個條件
                name = ticker.info.get('shortName', stock_id)
                current_price = closes[-1]
                
                alerts.append({
                    'code': stock_id,
                    'name': name,
                    'current_price': current_price,
                    'alert_reason': "、".join(reason)
                })
                
                # 控制 alert 數量
                if len(alerts) >= 10:
                    break
                
        except Exception as e:
            print(f"[stock_recommender] ⚠️ {stock_id} 極弱谷判斷失敗：{e}")
    
    return alerts

def send_recommendations_to_user(user_id, stocks, time_slot):
    """發送股票推薦訊息"""
    from modules.line_bot import send_line_bot_message
    
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

def send_weak_valley_alerts_to_user(user_id, weak_valleys):
    """發送極弱谷提醒"""
    from modules.line_bot import send_line_bot_message
    
    if not weak_valleys:
        return
    
    message = "【極弱谷警報】\n\n"
    for stock in weak_valleys:
        message += f"⚠️ {stock['code']} {stock['name']}\n"
        message += f"當前價格: {stock['current_price']}\n"
        message += f"警報原因: {stock['alert_reason']}\n\n"
    
    send_line_bot_message(message)
