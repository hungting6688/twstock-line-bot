"""
股票推薦分析模組

此模組提供多策略的股票推薦與風險分析功能，包括：
1. 不同時段的股票推薦策略
2. 弱勢股票預警
3. 多維度股票評估
"""

import numpy as np
import twstock
import pandas as pd
from datetime import datetime
import yfinance as yf

from modules.multi_analysis import analyze_stock_value
from modules.ta_analysis import analyze_technical_indicators
from modules.price_fetcher import get_top_stocks
from modules.twse_scraper import get_all_valid_twse_stocks
from modules.eps_dividend_scraper import get_eps_data, get_dividend_data
from modules.line_bot import send_line_bot_message

class StockRecommender:
    @staticmethod
    def get_stock_recommendations(time_slot, count=5):
        """
        根據時段獲取推薦股票
        
        Args:
            time_slot (str): 時段 ('morning', 'noon', 'afternoon', 'evening')
            count (int): 推薦股票數量
        
        Returns:
            list: 推薦股票列表
        """
        print(f"[stock_recommender] ⏳ 執行{time_slot}推薦分析...")
        
        strategies = {
            'morning': StockRecommender._morning_strategy,
            'noon': StockRecommender._noon_strategy,
            'afternoon': StockRecommender._afternoon_strategy,
            'evening': StockRecommender._evening_strategy
        }
        
        strategy_func = strategies.get(time_slot)
        return strategy_func(count) if strategy_func else []

    @staticmethod
    def _morning_strategy(count):
        """早盤前推薦策略"""
        all_stocks = get_all_valid_twse_stocks()
        
        print("[stock_recommender] 分析技術指標與基本面...")
        
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
        
        recommendations = []
        for candidate in top_candidates:
            try:
                ticker = yf.Ticker(f"{candidate['code']}.TW")
                history = ticker.history(period="1mo")
                
                if not history.empty:
                    current_price = history['Close'].iloc[-1]
                    ma_5 = history['Close'].tail(5).mean()
                    ma_10 = history['Close'].tail(10).mean()
                    
                    target_price = round(current_price * 1.05, 2)  # 目標漲幅5%
                    stop_loss = round(current_price * 0.97, 2)    # 止損點3%
                    
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

    @staticmethod
    def _noon_strategy(count):
        """中午休盤策略"""
        stock_ids = get_top_stocks(limit=100)
        tech_results = analyze_technical_indicators(stock_ids)
        
        sorted_results = sorted([
            (sid, data) for sid, data in tech_results.items()
        ], key=lambda x: x[1]['score'], reverse=True)
        
        recommendations = []
        for sid, data in sorted_results[:count]:
            try:
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

    @staticmethod
    def _afternoon_strategy(count):
        """尾盤前推薦策略"""
        stock_ids = get_top_stocks(limit=150)
        tech_results = analyze_technical_indicators(stock_ids)
        
        breakout_candidates = []
        for sid, data in tech_results.items():
            if data['score'] >= 5 and "均線" in data['desc'] and "KD" in data['desc']:
                try:
                    ticker = yf.Ticker(f"{sid}.TW")
                    history = ticker.history(period="5d")
                    
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
        
        breakout_candidates.sort(key=lambda x: x['score'], reverse=True)
        
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

    @staticmethod
    def _evening_strategy(count):
        """盤後分析推薦策略"""
        stock_ids = get_top_stocks(limit=200)
        tech_results = analyze_technical_indicators(stock_ids)
        eps_data = get_eps_data()
        
        candidates = []
        for sid, data in tech_results.items():
            if data['score'] >= 5:
                try:
                    ticker = yf.Ticker(f"{sid}.TW")
                    info = ticker.info
                    history = ticker.history(period="1mo")
                    
                    if history.empty:
                        continue
                    
                    name = info.get('shortName', sid)
                    current_price = history['Close'].iloc[-1]
                    
                    eps_info = eps_data.get(sid, {})
                    eps = eps_info.get('eps', 0)
                    dividend = eps_info.get('dividend', 0)
                    
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
        
        candidates.sort(key=lambda x: x['total_score'], reverse=True)
        
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

    @staticmethod
    def get_weak_valley_alerts():
        """
        識別處於極弱谷狀態的股票
        
        Returns:
            list: 極弱谷股票列表
        """
        print("[stock_recommender] ⏳ 掃描極弱谷股票...")
        
        stock_ids = get_top_stocks(limit=300)
        alerts = []
        
        for stock_id in stock_ids:
            try:
                ticker = yf.Ticker(f"{stock_id}.TW")
                history = ticker.history(period="60d")
                
                if history.empty or len(history) < 20:
                    continue
                
                closes = history['Close'].values
                
                # RSI 計算
                delta = np.diff(closes)
                up = np.sum([d if d > 0 else 0 for d in delta[-14:]])
                down = np.sum([abs(d) if d < 0 else 0 for d in delta[-14:]])
                rsi = 100 - (100 / (1 + (up / (down or 1))))
                
                # 均線計算
                ma_5 = np.mean(closes[-5:])
                ma_10 = np.mean(closes[-10:])
                ma_20 = np.mean(closes[-20:])
                
                # 連續下跌天數
                days_falling = sum(1 for i in range(len(closes)-1, 0, -1) 
                                   if closes[i] < closes[i-1]) 
                
                # 判斷極弱谷條件
                reason = []
                
                if rsi < 30:
                    reason.append(f"RSI={rsi:.1f}處於超賣區間")
                
                if closes[-1] < ma_20 * 0.95:
                    reason.append("股價跌破20日均線5%以上")
                
                if days_falling >= 4:
                    reason.append(f"連續下跌{days_falling}天")
                
                # 綜合判斷
                if len(reason) >= 2:  # 至少滿足兩個條件
                    name = ticker.info.get('shortName', stock_id)
                    current_price = closes[-1]
                    
                    alerts.append({
                        'code': stock_id,
                        'name': name,
                        'current_price': current_price,
                        'alert_reason': "、".join(reason)
                    })
                    
                    if len(alerts) >= 10:
                        break
                
            except Exception as e:
                print(f"[stock_recommender] ⚠️ {stock_id} 極弱谷判斷失敗：{e}")
        
        return alerts

    @staticmethod
    def send_recommendations_to_user(user_id, stocks, time_slot):
        """
        發送股票推薦訊息
        
        Args:
            user_id (str): 用戶ID
            stocks (list): 推薦股票列表
            time_slot (str): 時段
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

    @staticmethod
    def send_weak_valley_alerts_to_user(user_id, weak_valleys):
        """
        發送極弱谷提醒
        
        Args:
            user_id (str): 用戶ID
            weak_valleys (list): 極弱谷股票列表
        """
        if not weak_valleys:
            return
        
        message = "【極弱谷警報】\n\n"
        for stock in weak_valleys:
            message += f"⚠️ {stock['code']} {stock['name']}\n"
            message += f"當前價格: {stock['current_price']}\n"
            message += f"警報原因: {stock['alert_reason']}\n\n"
        
        send_line_bot_message(message)

# 快速訪問的別名函數
def get_stock_recommendations(time_slot, count=5):
    """
    快速獲取股票推薦的便捷函數
    
    Args:
        time_slot (str): 時段 ('morning', 'noon', 'afternoon', 'evening')
        count (int): 推薦股票數量
    
    Returns:
        list: 推薦股票列表
    """
    return StockRecommender.get_stock_recommendations(time_slot, count)

def get_weak_valley_alerts():
    """
    快速獲取極弱谷股票警報的便捷函數
    
    Returns:
        list: 極弱谷股票列表
    """
    return StockRecommender.get_weak_valley_alerts()

def send_recommendations_to_user(user_id, stocks, time_slot):
    """
    發送股票推薦訊息的便捷函數
    
    Args:
        user_id (str): 用戶ID
        stocks (list): 推薦股票列表
        time_slot (str): 時段
    """
    StockRecommender.send_recommendations_to_user(user_id, stocks, time_slot)

def send_weak_valley_alerts_to_user(user_id, weak_valleys):
    """
    發送極弱谷提醒的便捷函數
    
    Args:
        user_id (str): 用戶ID
        weak_valleys (list): 極弱谷股票列表
    """
    StockRecommender.send_weak_valley_alerts_to_user(user_id, weak_valleys)

print("[recommender] ✅ 已載入最新版")
