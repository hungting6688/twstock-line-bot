"""
股票推薦生成模組 - 支持多種策略選股
"""
import os
import json
import traceback
import yfinance as yf
from datetime import datetime, timedelta

# 修正導入路徑
from modules.data.fetcher import get_top_stocks
from modules.data.scraper import get_eps_data
from modules.analysis.technical import analyze_technical_indicators

# 直接定義 CACHE_DIR 而不是導入
CACHE_DIR = os.path.join(os.path.dirname(__file__), '../../cache')
os.makedirs(CACHE_DIR, exist_ok=True)

class StockRecommender:
    """
    股票推薦系統，提供多種選股策略
    """
    
    @staticmethod
    def _morning_strategy(count=5):
        """
        早盤前策略: 關注前一天收漲且技術指標偏多的股票
        """
        # 掃描限制
        scan_limit = 40
        
        # 獲取熱門股票
        stock_ids = get_top_stocks(limit=scan_limit)
        
        # 分析技術指標
        tech_results = analyze_technical_indicators(stock_ids)
        
        # 篩選符合條件的股票
        candidates = []
        for sid, data in tech_results.items():
            # 早盤策略: KD曲線向上，RSI > 50，MACD > 0
            if data.get('RSI', 0) > 50 and data.get('score', 0) >= 3:
                try:
                    ticker = yf.Ticker(f"{sid}.TW")
                    info = ticker.info
                    history = ticker.history(period="1mo")
                    
                    if history.empty:
                        continue
                        
                    name = info.get('shortName', sid)
                    current_price = history['Close'].iloc[-1]
                    
                    # 計算目標價和止損價
                    target_price = round(current_price * 1.05, 2)  # 上漲5%
                    stop_loss = round(current_price * 0.97, 2)     # 下跌3%
                    
                    candidates.append({
                        'code': sid,
                        'name': name,
                        'reason': data.get('desc', '技術指標強勢'),
                        'target_price': target_price,
                        'stop_loss': stop_loss,
                        'current_price': current_price
                    })
                except Exception as e:
                    print(f"[stock_recommender] ⚠️ {sid} 分析失敗：{e}")
        
        # 排序並限制數量
        candidates.sort(key=lambda x: x.get('current_price', 0) / x.get('stop_loss', 1), reverse=True)  # 風險報酬比排序
        
        return candidates[:count]
    
    @staticmethod
    def _noon_strategy(count=3):
        """
        午盤策略: 關注上午交易量增加且呈現多頭排列的股票
        """
        # 掃描限制
        scan_limit = 30
        
        # 獲取熱門股票
        stock_ids = get_top_stocks(limit=scan_limit)
        
        # 分析技術指標
        tech_results = analyze_technical_indicators(stock_ids)
        
        # 篩選符合條件的股票
        candidates = []
        for sid, data in tech_results.items():
            # 技術指標得分高且符合午盤策略的股票
            if '均線多頭排列' in data.get('desc', '') and data.get('score', 0) >= 3:
                try:
                    ticker = yf.Ticker(f"{sid}.TW")
                    info = ticker.info
                    history = ticker.history(period="1mo")
                    
                    if history.empty:
                        continue
                        
                    name = info.get('shortName', sid)
                    current_price = history['Close'].iloc[-1]
                    
                    # 計算目標價和止損價
                    target_price = round(current_price * 1.05, 2)  # 上漲5%
                    stop_loss = round(current_price * 0.97, 2)     # 下跌3%
                    
                    candidates.append({
                        'code': sid,
                        'name': name,
                        'reason': data.get('desc', '技術指標強勢'),
                        'target_price': target_price,
                        'stop_loss': stop_loss,
                        'current_price': current_price
                    })
                except Exception as e:
                    print(f"[stock_recommender] ⚠️ {sid} 分析失敗：{e}")
        
        # 排序並限制數量
        candidates.sort(key=lambda x: x.get('current_price', 0) / x.get('stop_loss', 1), reverse=True)  # 風險報酬比排序
        
        return candidates[:count]
    
    @staticmethod
    def _afternoon_strategy(count=3):
        """
        下午策略: 關注突破盤整且交易量放大的股票
        """
        # 掃描限制
        scan_limit = 30
        
        # 獲取熱門股票
        stock_ids = get_top_stocks(limit=scan_limit)
        
        # 分析技術指標
        tech_results = analyze_technical_indicators(stock_ids)
        
        # 篩選符合條件的股票
        candidates = []
        for sid, data in tech_results.items():
            # 下午策略: 突破盤整，交易量放大
            if '突破盤整' in data.get('desc', '') and data.get('score', 0) >= 3:
                try:
                    ticker = yf.Ticker(f"{sid}.TW")
                    info = ticker.info
                    history = ticker.history(period="1mo")
                    
                    if history.empty:
                        continue
                        
                    name = info.get('shortName', sid)
                    current_price = history['Close'].iloc[-1]
                    
                    # 計算目標價和止損價
                    target_price = round(current_price * 1.04, 2)  # 上漲4%
                    stop_loss = round(current_price * 0.97, 2)     # 下跌3%
                    
                    candidates.append({
                        'code': sid,
                        'name': name,
                        'reason': data.get('desc', '突破盤整'),
                        'target_price': target_price,
                        'stop_loss': stop_loss,
                        'current_price': current_price
                    })
                except Exception as e:
                    print(f"[stock_recommender] ⚠️ {sid} 分析失敗：{e}")
        
        # 排序並限制數量
        candidates.sort(key=lambda x: x.get('current_price', 0) / x.get('stop_loss', 1), reverse=True)  # 風險報酬比排序
        
        return candidates[:count]
    
    @staticmethod
    def _evening_strategy(count=5):
        """
        盤後策略: 關注當日表現良好，技術指標多頭的股票
        """
        # 掃描限制
        scan_limit = 50
        
        # 獲取熱門股票
        stock_ids = get_top_stocks(limit=scan_limit)
        
        # 分析技術指標
        tech_results = analyze_technical_indicators(stock_ids)
        
        # 篩選符合條件的股票
        candidates = []
        for sid, data in tech_results.items():
            # 盤後策略: 技術指標良好，當日表現不錯
            if data.get('score', 0) >= 4:
                try:
                    ticker = yf.Ticker(f"{sid}.TW")
                    info = ticker.info
                    history = ticker.history(period="1mo")
                    
                    if history.empty:
                        continue
                        
                    name = info.get('shortName', sid)
                    current_price = history['Close'].iloc[-1]
                    
                    # 計算目標價和止損價
                    target_price = round(current_price * 1.07, 2)  # 上漲7%
                    stop_loss = round(current_price * 0.95, 2)     # 下跌5%
                    
                    candidates.append({
                        'code': sid,
                        'name': name,
                        'reason': data.get('desc', '技術指標強勢'),
                        'target_price': target_price,
                        'stop_loss': stop_loss,
                        'current_price': current_price
                    })
                except Exception as e:
                    print(f"[stock_recommender] ⚠️ {sid} 分析失敗：{e}")
        
        # 排序並限制數量
        candidates.sort(key=lambda x: x.get('current_price', 0) / x.get('stop_loss', 1), reverse=True)  # 風險報酬比排序
        
        return candidates[:count]
    
    @staticmethod
    def get_weak_valley_alerts(count=2):
        """
        獲取技術極弱股警示
        """
        # 掃描限制
        scan_limit = 50
        
        # 獲取熱門股票
        stock_ids = get_top_stocks(limit=scan_limit)
        
        # 分析技術指標
        tech_results = analyze_technical_indicators(stock_ids)
        
        # 篩選符合條件的股票
        candidates = []
        for sid, data in tech_results.items():
            # 極弱股條件：RSI < 30, 技術指標得分低，跌破支撐
            if data.get('RSI', 99) < 30 or data.get('score', 5) <= 1 or '跌破支撐' in data.get('desc', ''):
                try:
                    ticker = yf.Ticker(f"{sid}.TW")
                    info = ticker.info
                    history = ticker.history(period="1mo")
                    
                    if history.empty:
                        continue
                        
                    name = info.get('shortName', sid)
                    current_price = history['Close'].iloc[-1]
                    
                    # 警報原因
                    alert_reasons = []
                    if data.get('RSI', 99) < 30:
                        alert_reasons.append(f"RSI低迷({data.get('RSI', 0):.1f})")
                    if '跌破支撐' in data.get('desc', ''):
                        alert_reasons.append('跌破重要支撐')
                    if data.get('score', 5) <= 1:
                        alert_reasons.append('技術指標極弱')
                    
                    alert_reason = "、".join(alert_reasons)
                    
                    candidates.append({
                        'code': sid,
                        'name': name,
                        'alert_reason': alert_reason,
                        'current_price': current_price
                    })
                except Exception as e:
                    print(f"[stock_recommender] ⚠️ {sid} 弱勢分析失敗：{e}")
        
        # 排序並限制數量 (按RSI值升序排序)
        candidates.sort(key=lambda x: tech_results.get(x['code'], {}).get('RSI', 50))
        
        return candidates[:count]
    
    @staticmethod
    def get_multi_strategy_recommendations(time_slot="morning", count=None):
        """
        獲取多策略股票推薦 (短線、長線、極弱股)
        
        Args:
            time_slot (str): 時段 ('morning', 'noon', 'afternoon', 'evening')
            count (int): 每種策略的推薦股票數量
        
        Returns:
            dict: 包含三種策略的推薦股票字典
        """
        print(f"[stock_recommender] ⏳ 執行{time_slot}多策略分析...")
        
        # 根據時段設置每類推薦數量
        if count is None:
            if time_slot == 'morning':
                short_term_count = 5  # 早盤前短線推薦5檔
                long_term_count = 3   # 早盤前長線推薦3檔
                weak_stock_count = 2  # 早盤前極弱股2檔
            elif time_slot == 'noon':
                short_term_count = 4
                long_term_count = 2
                weak_stock_count = 1
            elif time_slot == 'afternoon':
                short_term_count = 4
                long_term_count = 2
                weak_stock_count = 1
            elif time_slot == 'evening':
                short_term_count = 5
                long_term_count = 5
                weak_stock_count = 2
            else:
                short_term_count = 3
                long_term_count = 3
                weak_stock_count = 1
        else:
            short_term_count = count
            long_term_count = count
            weak_stock_count = min(count, 2)  # 極弱股最多2檔，避免過多負面訊息
        
        # 檢查緩存
        cache_file = os.path.join(CACHE_DIR, f'multi_strategy_{time_slot}_cache.json')
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    cache_time = datetime.fromisoformat(cache_data['timestamp'])
                    
                    # 如果緩存時間不超過30分鐘，直接使用緩存
                    if (datetime.now() - cache_time).total_seconds() < 1800:  # 30分鐘
                        print(f"[stock_recommender] ✅ 使用緩存的{time_slot}多策略推薦")
                        return cache_data['recommendations']
            except Exception as e:
                print(f"[stock_recommender] ⚠️ 讀取多策略推薦緩存失敗: {e}")
        
        # 獲取各策略推薦
        try:
            # 1. 獲取短線推薦
            short_term_stocks = StockRecommender._short_term_strategy(short_term_count, time_slot)
            
            # 2. 獲取長線推薦
            long_term_stocks = StockRecommender._long_term_strategy(long_term_count, time_slot)
            
            # 3. 獲取極弱股警示
            weak_stocks = StockRecommender.get_weak_valley_alerts(weak_stock_count)
            
            # 整合結果
            recommendations = {
                "short_term": short_term_stocks,
                "long_term": long_term_stocks,
                "weak_stocks": weak_stocks
            }
            
            # 儲存推薦結果到緩存
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    cache_data = {
                        'timestamp': datetime.now().isoformat(),
                        'recommendations': recommendations
                    }
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                print(f"[stock_recommender] ✅ 已緩存{time_slot}多策略推薦結果")
            except Exception as e:
                print(f"[stock_recommender] ⚠️ 寫入多策略推薦緩存失敗: {e}")
            
            return recommendations
        except Exception as e:
            print(f"[stock_recommender] ❌ 多策略分析失敗: {e}")
            traceback.print_exc()
            return {"short_term": [], "long_term": [], "weak_stocks": []}

    @staticmethod
    def _short_term_strategy(count, time_slot):
        """
        短線推薦策略 (RSI > 50、KD 金叉、MACD 翻多、布林突破)
        使用現有的 morning_strategy、noon_strategy 等作為短線策略的基礎
        """
        # 優先使用現有策略函數
        existing_strategies = {
            'morning': StockRecommender._morning_strategy,
            'noon': StockRecommender._noon_strategy,
            'afternoon': StockRecommender._afternoon_strategy,
            'evening': StockRecommender._evening_strategy
        }
        
        strategy_func = existing_strategies.get(time_slot)
        if strategy_func:
            return strategy_func(count)
        
        # 如果沒有對應的現有策略，使用通用短線策略
        # 掃描限制
        scan_limit = 50
        
        # 獲取熱門股票
        stock_ids = get_top_stocks(limit=scan_limit)
        
        # 分析技術指標
        tech_results = analyze_technical_indicators(stock_ids)
        
        # 篩選符合短線條件的股票
        candidates = []
        for sid, data in tech_results.items():
            # 短線條件: RSI > 50、KD 金叉、MACD 翻多、均線支撐
            if data.get('RSI', 0) > 50 and 'KD黃金交叉' in data.get('desc', '') and data.get('score', 0) >= 3:
                try:
                    ticker = yf.Ticker(f"{sid}.TW")
                    info = ticker.info
                    history = ticker.history(period="1mo")
                    
                    if history.empty:
                        continue
                        
                    name = info.get('shortName', sid)
                    current_price = history['Close'].iloc[-1]
                    
                    # 計算目標價和止損價
                    target_price = round(current_price * 1.05, 2)  # 上漲5%
                    stop_loss = round(current_price * 0.97, 2)     # 下跌3%
                    
                    candidates.append({
                        'code': sid,
                        'name': name,
                        'reason': data.get('desc', '技術指標強勢'),
                        'target_price': target_price,
                        'stop_loss': stop_loss,
                        'current_price': current_price
                    })
                except Exception as e:
                    print(f"[stock_recommender] ⚠️ {sid} 短線分析失敗：{e}")
        
        # 排序並限制數量
        candidates.sort(key=lambda x: x.get('current_price', 0) / x.get('stop_loss', 1), reverse=True)  # 風險報酬比排序
        
        return candidates[:count]

    @staticmethod
    def _long_term_strategy(count, time_slot):
        """
        長線推薦策略 (EPS > 2、殖利率 ≥ 4%、本益比 < 15、法人買超、MACD 翻多)
        """
        # 掃描限制
        scan_limit = 100
        
        # 獲取熱門股票
        stock_ids = get_top_stocks(limit=scan_limit)
        
        # 獲取 EPS 和股息數據
        try:
            eps_data = get_eps_data(use_cache=True, cache_expiry_hours=72)
        except Exception as e:
            print(f"[stock_recommender] ⚠️ 獲取 EPS 數據失敗: {e}")
            eps_data = {}
        
        # 分析技術指標
        tech_results = analyze_technical_indicators(stock_ids)
        
        # 篩選符合長線條件的股票
        candidates = []
        for sid, data in tech_results.items():
            # 檢查基本面
            eps_info = eps_data.get(sid, {})
            eps = eps_info.get('eps', 0)
            dividend = eps_info.get('dividend', 0)
            
            # 長線條件: EPS>2、殖利率≥4%、技術指標良好
            long_term_score = 0
            reasons = []
            
            # EPS 評分
            if eps and eps > 5:
                long_term_score += 2
                reasons.append(f"EPS {eps} 元優異")
            elif eps and eps > 2:
                long_term_score += 1
                reasons.append(f"EPS {eps} 元良好")
            
            # 股息率評分
            if dividend and dividend >= 4:
                long_term_score += 2
                reasons.append(f"殖利率 {dividend}% 豐厚")
            elif dividend and dividend >= 2.5:
                long_term_score += 1
                reasons.append(f"殖利率 {dividend}% 不錯")
            
            # 技術面評分
            if data.get('score', 0) >= 4:
                long_term_score += 2
                reasons.append(data.get('desc', '技術指標強勢'))
            elif data.get('score', 0) >= 2:
                long_term_score += 1
                reasons.append(data.get('desc', '技術指標尚可'))
            
            # 評分達標才納入候選
            if long_term_score >= 3:
                try:
                    ticker = yf.Ticker(f"{sid}.TW")
                    info = ticker.info
                    history = ticker.history(period="1mo")
                    
                    if history.empty:
                        continue
                        
                    name = info.get('shortName', sid)
                    current_price = history['Close'].iloc[-1]
                    
                    # 獲取本益比
                    pe_ratio = info.get('trailingPE')
                    if pe_ratio and pe_ratio < 15:
                        long_term_score += 1
                        reasons.append(f"本益比 {pe_ratio:.1f} 合理")
                    
                    # 計算目標價和止損價
                    target_price = round(current_price * 1.15, 2)  # 上漲15%
                    stop_loss = round(current_price * 0.90, 2)     # 下跌10%
                    
                    candidates.append({
                        'code': sid,
                        'name': name,
                        'reason': "、".join(reasons),
                        'target_price': target_price,
                        'stop_loss': stop_loss,
                        'current_price': current_price,
                        'score': long_term_score
                    })
                except Exception as e:
                    print(f"[stock_recommender] ⚠️ {sid} 長線分析失敗：{e}")
        
        # 排序並限制數量
        candidates.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return candidates[:count]


def get_stock_recommendations(time_slot="morning", count=3):
    """
    獲取股票推薦的便捷函數
    
    Args:
        time_slot (str): 時段 ('morning', 'noon', 'afternoon', 'evening')
        count (int): 推薦股票數量
    
    Returns:
        list: 推薦股票列表
    """
    existing_strategies = {
        'morning': StockRecommender._morning_strategy,
        'noon': StockRecommender._noon_strategy,
        'afternoon': StockRecommender._afternoon_strategy,
        'evening': StockRecommender._evening_strategy
    }
    
    strategy_func = existing_strategies.get(time_slot, StockRecommender._morning_strategy)
    return strategy_func(count)


def get_multi_strategy_recommendations(time_slot="morning", count=None):
    """
    獲取多策略股票推薦的便捷函數
    
    Args:
        time_slot (str): 時段 ('morning', 'noon', 'afternoon', 'evening')
        count (int): 每種策略的推薦股票數量
    
    Returns:
        dict: 包含三種策略的推薦股票字典
    """
    return StockRecommender.get_multi_strategy_recommendations(time_slot, count)


def get_weak_stock_alerts(count=2):
    """
    獲取極弱股警示的便捷函數
    
    Args:
        count (int): 警示股票數量
    
    Returns:
        list: 極弱股警示列表
    """
    return StockRecommender.get_weak_valley_alerts(count)
