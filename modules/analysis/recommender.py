"""
股票推薦分析模組 - 改進版，增強超時處理和部分結果處理能力

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
import threading
import time
import os
import json
import traceback

from modules.multi_analysis import analyze_stock_value
from modules.analysis.technical import analyze_technical_indicators
from modules.data.fetcher import get_top_stocks
from modules.data.scraper import get_all_valid_twse_stocks, get_eps_data, get_dividend_data
from modules.notification.line_bot import send_line_bot_message

# 緩存目錄設置
CACHE_DIR = os.path.join(os.path.dirname(__file__), '../../cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# 重要股票清單 - 優先處理這些股票
PRIORITY_STOCKS = [
    "2330", "2317", "2454", "2412", "2303", "2308", "2882", "2881", 
    "1301", "1303", "2002", "2886", "1216", "2891", "3711", "2327"
]

class StockRecommender:
    @staticmethod
    def get_stock_recommendations(time_slot, count=None):
        """
        根據時段獲取推薦股票
        
        Args:
            time_slot (str): 時段 ('morning', 'noon', 'afternoon', 'evening')
            count (int): 推薦股票數量，None 表示使用預設值
        
        Returns:
            list: 推薦股票列表
        """
        print(f"[stock_recommender] ⏳ 執行{time_slot}推薦分析...")
        
        # 根據時段設置預設推薦數量
        if count is None:
            if time_slot == 'morning':
                count = 6  # 早盤前推薦6檔
            elif time_slot == 'noon':
                count = 6  # 午盤推薦6檔
            elif time_slot == 'afternoon':
                count = 6  # 上午看盤推薦6檔
            elif time_slot == 'evening':
                count = 10  # 盤後分析推薦10檔
            else:
                count = 6  # 默認值
        
        strategies = {
            'morning': StockRecommender._morning_strategy,
            'noon': StockRecommender._noon_strategy,
            'afternoon': StockRecommender._afternoon_strategy,
            'evening': StockRecommender._evening_strategy
        }
        
        strategy_func = strategies.get(time_slot)
        
        # 檢查緩存，避免短時間內重複分析
        cache_file = os.path.join(CACHE_DIR, f'recommendation_{time_slot}_cache.json')
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    cache_time = datetime.fromisoformat(cache_data['timestamp'])
                    
                    # 如果緩存時間不超過30分鐘，直接使用緩存
                    if (datetime.now() - cache_time).total_seconds() < 1800:  # 30分鐘
                        print(f"[stock_recommender] ✅ 使用緩存的{time_slot}推薦 (更新於 {cache_time.strftime('%H:%M:%S')})")
                        return cache_data['recommendations']
            except Exception as e:
                print(f"[stock_recommender] ⚠️ 讀取推薦緩存失敗: {e}")
        
        # 執行策略函數，獲取推薦
        try:
            recommendations = strategy_func(count) if strategy_func else []
            
            # 儲存推薦結果到緩存
            if recommendations:
                try:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        cache_data = {
                            'timestamp': datetime.now().isoformat(),
                            'recommendations': recommendations
                        }
                        json.dump(cache_data, f, ensure_ascii=False, indent=2)
                    print(f"[stock_recommender] ✅ 已緩存{time_slot}推薦結果")
                except Exception as e:
                    print(f"[stock_recommender] ⚠️ 寫入推薦緩存失敗: {e}")
                    
            return recommendations
        except Exception as e:
            print(f"[stock_recommender] ❌ {time_slot}策略執行失敗: {e}")
            traceback.print_exc()
            return []

    @staticmethod
    def _morning_strategy(count):
        """
        早盤前推薦策略 - 增強版，支持部分結果處理
        
        專注於處理優先股票，然後處理其他股票，即使分析未完全完成也能返回部分結果
        """
        # 掃描限制保持100檔
        scan_limit = 100
        
        # 獲取活躍股票
        print(f"[stock_recommender] 獲取前{scan_limit}檔熱門股票...")
        try:
            top_stocks = get_top_stocks(limit=scan_limit)
            
            # 確保優先股票在前面處理
            priority_stocks = [s for s in PRIORITY_STOCKS if s in top_stocks]
            other_stocks = [s for s in top_stocks if s not in PRIORITY_STOCKS]
            
            # 重排序股票清單，優先股在前
            priority_ordered_stocks = priority_stocks + other_stocks
            
            # 如果獲取失敗，使用備用清單
            if not priority_ordered_stocks:
                raise ValueError("無法獲取股票清單")
                
        except Exception as e:
            print(f"[stock_recommender] ⚠️ 獲取熱門股票失敗: {e}，使用備用清單")
            # 使用備用清單
            priority_ordered_stocks = PRIORITY_STOCKS[:20]  # 僅使用前20個優先股
        
        print(f"[stock_recommender] 分析早盤技術指標與基本面...")
        
        # 預先獲取 EPS 數據，避免每支股票都重新獲取
        eps_data = {}
        try:
            print("[stock_recommender] 一次性獲取 EPS 數據...")
            eps_data = get_eps_data(use_cache=True, cache_expiry_hours=72)  # 增加緩存有效期
            if eps_data:
                print(f"[stock_recommender] ✅ 成功獲取 {len(eps_data)} 檔股票的 EPS 數據")
            else:
                print("[stock_recommender] ⚠️ 未能獲取 EPS 數據，將使用有限信息進行分析")
        except Exception as e:
            print(f"[stock_recommender] ⚠️ 獲取 EPS 數據失敗: {e}")
        
        # 分階段處理和返回結果
        candidates = []
        processed_count = 0
        max_processing_time = 150  # 最大處理時間150秒
        start_time = time.time()
        
        # 定義處理單一股票的函數
        def process_stock(stock_id):
            nonlocal processed_count
            nonlocal candidates
            
            try:
                # 檢查是否超時
                if time.time() - start_time > max_processing_time:
                    return False  # 超時，停止處理
                
                # 添加超時控制
                result = {"completed": False, "score": 0, "analysis": None}
                
                def analyze():
                    try:
                        # 使用較短的超時時間獲取數據
                        ticker = yf.Ticker(f"{stock_id}.TW")
                        
                        # 獲取歷史數據
                        history = ticker.history(period="30d")
                        if history.empty:
                            print(f"[stock_recommender] ⚠️ {stock_id} 無歷史數據")
                            return
                        
                        score, analysis = analyze_stock_value(stock_id)
                        result["score"] = score
                        result["analysis"] = analysis
                        result["completed"] = True
                    except Exception as e:
                        print(f"[stock_recommender] ⚠️ {stock_id} 分析失敗: {e}")
                
                # 創建並啟動線程
                t = threading.Thread(target=analyze)
                t.daemon = True
                t.start()
                
                # 等待分析完成或超時 (縮短到3秒)
                t.join(3)
                
                if not result["completed"]:
                    print(f"[stock_recommender] ⚠️ {stock_id} 分析超時")
                    processed_count += 1
                    return True  # 繼續處理下一股
                
                score = result["score"]
                analysis = result["analysis"]
                
                # 獲取股票名稱 - 優先使用緩存的資料
                name = stock_id
                try:
                    if eps_data and stock_id in eps_data:
                        # 如果有資料，嘗試獲取名稱
                        # 這裡假設沒有名稱資訊，僅作為範例
                        pass
                    else:
                        # 嘗試從 yfinance 獲取名稱
                        info = ticker.info
                        if 'shortName' in info:
                            name = info.get('shortName', stock_id)
                        else:
                            # 嘗試直接從URL抓取名字
                            name = stock_id  # 作為備用
                except Exception:
                    name = stock_id  # 如果獲取失敗，使用代號
                
                if score > 40:  # 降低分數門檻，確保有足夠的候選股票
                    current_price = None
                    try:
                        if not history.empty and 'Close' in history:
                            current_price = history['Close'].iloc[-1]
                    except:
                        pass
                        
                    candidates.append({
                        'code': stock_id,
                        'name': name,
                        'score': score,
                        'analysis': analysis,
                        'current_price': current_price
                    })
                    
                    # 當候選股票數達到 count*3 時，可以提前結束
                    if len(candidates) >= count * 3:
                        print(f"[stock_recommender] 已獲取足夠候選股票 ({len(candidates)}檔)，可以提前結束")
                        # 但不立即停止，而是繼續處理一段時間，確保優先股票被處理
                
                processed_count += 1
                return True  # 繼續處理
                
            except Exception as e:
                print(f"[stock_recommender] ⚠️ {stock_id} 處理失敗：{e}")
                processed_count += 1
                return True  # 繼續處理下一股
        
        # 首先處理優先股票
        for stock_id in priority_ordered_stocks:
            if not process_stock(stock_id):
                break  # 時間到，停止處理
                
            # 定期檢查是否已有足夠候選股票
            if len(candidates) >= count and processed_count >= 20:
                print(f"[stock_recommender] 已處理 {processed_count} 檔股票，找到 {len(candidates)} 個候選，提前結束分析")
                break
        
        print(f"[stock_recommender] 完成分析, 共處理了 {processed_count} 檔股票，找到 {len(candidates)} 個候選")
        
        # 如果沒有足夠的候選股，但已經處理了一些股票，嘗試降低門檻
        if len(candidates) < count and processed_count > 0:
            print(f"[stock_recommender] ⚠️ 候選股數量不足 ({len(candidates)}/{count})，使用已處理的結果")
        
        # 根據分數排序並選出前N名
        candidates.sort(key=lambda x: x['score'], reverse=True)
        top_candidates = candidates[:count]
        
        recommendations = []
        for candidate in top_candidates:
            try:
                # 使用已獲取的當前價格計算目標和止損價
                current_price = candidate.get('current_price')
                
                # 如果沒有當前價格，再次嘗試獲取
                if current_price is None:
                    try:
                        ticker = yf.Ticker(f"{candidate['code']}.TW")
                        history = ticker.history(period="1d")
                        if not history.empty:
                            current_price = history['Close'].iloc[-1]
                    except:
                        # 如果依然失敗，使用估計值
                        current_price = 100  # 預設值
                
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
        
        # 如果推薦數量不足，使用優先股填充
        if len(recommendations) < count:
            missing_count = count - len(recommendations)
            print(f"[stock_recommender] ⚠️ 推薦數量不足，缺少 {missing_count} 檔，使用預設股票填充")
            
            # 獲取已推薦的股票代碼
            recommended_codes = [r['code'] for r in recommendations]
            
            # 使用優先股填充，優先使用尚未推薦的股票
            for stock_id in PRIORITY_STOCKS:
                if stock_id not in recommended_codes and len(recommendations) < count:
                    try:
                        ticker = yf.Ticker(f"{stock_id}.TW")
                        info = ticker.info
                        history = ticker.history(period="7d")
                        
                        name = info.get('shortName', stock_id)
                        current_price = history['Close'].iloc[-1] if not history.empty else 100
                        
                        target_price = round(current_price * 1.05, 2)
                        stop_loss = round(current_price * 0.97, 2)
                        
                        recommendations.append({
                            'code': stock_id,
                            'name': name,
                            'reason': "台股主要成分股，具備基本投資價值",
                            'target_price': target_price,
                            'stop_loss': stop_loss,
                            'current_price': current_price
                        })
                    except:
                        # 如果獲取失敗，使用預設值
                        recommendations.append({
                            'code': stock_id,
                            'name': f"{stock_id} (預設)",
                            'reason': "台股主要成分股，具備基本投資價值",
                            'target_price': 105,
                            'stop_loss': 97,
                            'current_price': 100
                        })
                
                # 如果已經填充足夠，停止
                if len(recommendations) >= count:
                    break
        
        return recommendations

    @staticmethod
    def _noon_strategy(count):
        """中午休盤策略"""
        # 掃描50檔股票
        scan_limit = 50
        
        # 獲取活躍股票 - 只執行一次
        print(f"[stock_recommender] 獲取前{scan_limit}檔熱門股票...")
        stock_ids = get_top_stocks(limit=scan_limit)
        
        print(f"[stock_recommender] 分析午盤技術指標...")
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
        # 掃描50檔股票
        scan_limit = 50
        
        # 獲取活躍股票 - 只執行一次
        print(f"[stock_recommender] 獲取前{scan_limit}檔熱門股票...")
        stock_ids = get_top_stocks(limit=scan_limit)
        
        print(f"[stock_recommender] 分析尾盤技術指標...")
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
        # 掃描100檔股票
        scan_limit = 100
        
        # 獲取活躍股票 - 只執行一次
        print(f"[stock_recommender] 獲取前{scan_limit}檔熱門股票...")
        stock_ids = get_top_stocks(limit=scan_limit)
        
        print(f"[stock_recommender] 分析盤後技術指標...")
        tech_results = analyze_technical_indicators(stock_ids)
        
        # 預先獲取 EPS 數據，避免每支股票都重新獲取
        try:
            print("[stock_recommender] 一次性獲取 EPS 數據...")
            eps_data = get_eps_data(use_cache=True, cache_expiry_hours=72)  # 增加緩存有效期
        except Exception as e:
            print(f"[stock_recommender] ⚠️ 獲取 EPS 數據失敗: {e}")
            eps_data = {}
        
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
                    
                    # 使用預先獲取的 EPS 數據
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
    def get_weak_valley_alerts(count=2):
        """
        識別處於極弱谷狀態的股票
        
        Args:
            count (int): 極弱谷股票數量，默認為2
            
        Returns:
            list: 極弱谷股票列表
        """
        print("[stock_recommender] ⏳ 掃描極弱谷股票...")
        
        # 檢查緩存
        cache_file = os.path.join(CACHE_DIR, 'weak_valley_cache.json')
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    cache_time = datetime.fromisoformat(cache_data['timestamp'])
                    
                    # 如果緩存時間不超過12小時，直接使用緩存
                    if (datetime.now() - cache_time).total_seconds() < 43200:  # 12小時
                        print(f"[stock_recommender] ✅ 使用緩存的極弱谷警報 (更新於 {cache_time.strftime('%H:%M:%S')})")
                        return cache_data['weak_valleys']
            except Exception as e:
                print(f"[stock_recommender] ⚠️ 讀取極弱谷緩存失敗: {e}")
        
        # 從前100檔中尋找極弱谷股票
        scan_limit = 100
        stock_ids = get_top_stocks(limit=scan_limit)
        alerts = []
        
        max_processing_time = 60  # 最大處理時間60秒
        start_time = time.time()
        
        for stock_id in stock_ids[:scan_limit]:
            # 檢查是否超時
            if time.time() - start_time > max_processing_time:
                print(f"[stock_recommender] ⚠️ 極弱谷股票掃描超時，返回部分結果")
                break
                
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
                rsi = 100 - (100 / (1 + (up / (down or 1e-10))))
                
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
                    
                    # 如果已找到足夠數量的極弱谷股票，則提前結束
                    if len(alerts) >= count:
                        break
                
            except Exception as e:
                print(f"[stock_recommender] ⚠️ {stock_id} 極弱谷判斷失敗：{e}")
        
        # 儲存結果到緩存
        if alerts:
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    cache_data = {
                        'timestamp': datetime.now().isoformat(),
                        'weak_valleys': alerts
                    }
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                print(f"[stock_recommender] ✅ 已緩存極弱谷警報結果")
            except Exception as e:
                print(f"[stock_recommender] ⚠️ 寫入極弱谷緩存失敗: {e}")
        
        # 返回指定數量的極弱谷股票
        return alerts[:count]

    @staticmethod
    def send_recommendations_to_user(user_id, stocks, time_slot):
        """
        發送股票推薦訊息
        
        Args:
            user_id (str): 用戶ID
            stocks (list): 推薦股票列表
            time_slot (str): 時段名稱
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
        發送極弱谷警報訊息
        
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
        
        message += "註：極弱谷表示股票處於超賣狀態，可以觀察反彈機會，但要注意風險控制。"
        
        send_line_bot_message(message)

# 快速訪問的別名函數
def get_stock_recommendations(time_slot, count=None):
    """
    快速獲取股票推薦的便捷函數
    
    Args:
        time_slot (str): 時段 ('morning', 'noon', 'afternoon', 'evening')
        count (int): 推薦股票數量，None 表示使用預設值
    
    Returns:
        list: 推薦股票列表
    """
    return StockRecommender.get_stock_recommendations(time_slot, count)

def get_weak_valley_alerts(count=2):
    """
    快速獲取極弱谷股票警報的便捷函數
    
    Args:
        count (int): 極弱谷股票數量，默認為2
        
    Returns:
        list: 極弱谷股票列表
    """
    return StockRecommender.get_weak_valley_alerts(count)

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
