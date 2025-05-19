"""
多重分析模組 - 整合多種技術和基本面分析方法來評估股票
"""

print("[multi_analysis] ✅ 已載入最新版")

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import time
import threading

def analyze_stock_value(stock_code):
    """
    使用多重分析方法評估股票價值
    
    參數:
    - stock_code: 股票代碼
    
    返回:
    - score: 綜合評分 (0-100)
    - analysis: 分析詳情
    """
    print(f"[multi_analysis] 分析 {stock_code} 股票價值...")
    
    # 初始化各分析維度的權重
    weights = {
        'technical': 0.35,  # 技術面分析權重
        'fundamental': 0.30,  # 基本面分析權重
        'industry': 0.15,    # 產業趨勢權重
        'market_sentiment': 0.20  # 市場情緒權重
    }
    
    # 添加超時控制
    result = {
        "technical": {"completed": False, "score": 0, "analysis": "分析超時"},
        "fundamental": {"completed": False, "score": 0, "analysis": "分析超時"},
        "industry": {"completed": False, "score": 0, "analysis": "分析超時"},
        "market_sentiment": {"completed": False, "score": 0, "analysis": "分析超時"}
    }
    
    # 創建線程執行各維度分析
    threads = []
    
    # 技術面分析線程
    def run_technical():
        try:
            score, analysis = analyze_technical(stock_code)
            result["technical"] = {"completed": True, "score": score, "analysis": analysis}
        except Exception as e:
            print(f"[multi_analysis] ⚠️ 技術分析失敗：{e}")
            result["technical"] = {"completed": True, "score": 0, "analysis": f"技術分析失敗: {str(e)}"}
    
    # 基本面分析線程
    def run_fundamental():
        try:
            score, analysis = analyze_fundamental(stock_code)
            result["fundamental"] = {"completed": True, "score": score, "analysis": analysis}
        except Exception as e:
            print(f"[multi_analysis] ⚠️ 基本面分析失敗：{e}")
            result["fundamental"] = {"completed": True, "score": 0, "analysis": f"基本面分析失敗: {str(e)}"}
    
    # 產業分析線程
    def run_industry():
        try:
            score, analysis = analyze_industry(stock_code)
            result["industry"] = {"completed": True, "score": score, "analysis": analysis}
        except Exception as e:
            print(f"[multi_analysis] ⚠️ 產業分析失敗：{e}")
            result["industry"] = {"completed": True, "score": 0, "analysis": f"產業分析失敗: {str(e)}"}
    
    # 市場情緒分析線程
    def run_sentiment():
        try:
            score, analysis = analyze_market_sentiment(stock_code)
            result["market_sentiment"] = {"completed": True, "score": score, "analysis": analysis}
        except Exception as e:
            print(f"[multi_analysis] ⚠️ 市場情緒分析失敗：{e}")
            result["market_sentiment"] = {"completed": True, "score": 0, "analysis": f"市場情緒分析失敗: {str(e)}"}
    
    # 創建並啟動所有線程
    threads.append(threading.Thread(target=run_technical))
    threads.append(threading.Thread(target=run_fundamental))
    threads.append(threading.Thread(target=run_industry))
    threads.append(threading.Thread(target=run_sentiment))
    
    for t in threads:
        t.daemon = True
        t.start()
    
    # 等待線程完成或超時
    timeout = 10  # 每個分析最多等待 10 秒
    for t in threads:
        t.join(timeout)
    
    # 獲取各維度分析結果
    technical_score = result["technical"]["score"]
    technical_analysis = result["technical"]["analysis"]
    
    fundamental_score = result["fundamental"]["score"]
    fundamental_analysis = result["fundamental"]["analysis"]
    
    industry_score = result["industry"]["score"]
    industry_analysis = result["industry"]["analysis"]
    
    sentiment_score = result["market_sentiment"]["score"]
    sentiment_analysis = result["market_sentiment"]["analysis"]
    
    # 計算綜合評分
    total_score = (
        technical_score * weights['technical'] +
        fundamental_score * weights['fundamental'] +
        industry_score * weights['industry'] +
        sentiment_score * weights['market_sentiment']
    )
    
    # 匯總分析結果
    analysis = {
        'technical': technical_analysis,
        'fundamental': fundamental_analysis,
        'industry': industry_analysis,
        'market_sentiment': sentiment_analysis,
    }
    
    print(f"[multi_analysis] {stock_code} 總評分: {total_score:.1f}/100")
    
    return total_score, analysis

def analyze_technical(stock_code):
    """技術面分析，增加錯誤處理和空值檢查"""
    # 使用 yfinance 取得股價資料
    try:
        ticker = yf.Ticker(f"{stock_code}.TW")
        history = ticker.history(period="60d")
        
        if history.empty or len(history) < 30:
            return 0, "歷史資料不足"
        
        # 提取收盤價和成交量並進行檢查
        if 'Close' not in history.columns:
            return 0, "無收盤價資料"
            
        closes = history['Close'].values
        if len(closes) < 30:
            return 0, "收盤價資料不足"
            
        volumes = history['Volume'].values if 'Volume' in history.columns else np.zeros(len(closes))
        
        # 計算技術指標前先檢查數據
        if len(closes) < 60:
            # 確保有足夠的資料長度
            padding = np.zeros(60 - len(closes))
            closes = np.concatenate([padding, closes])
            volumes = np.concatenate([padding, volumes])
        
        # 1. 移動平均線
        ma_5 = np.mean(closes[-5:])
        ma_10 = np.mean(closes[-10:])
        ma_20 = np.mean(closes[-20:])
        ma_60 = np.mean(closes[-60:])
        
        # 2. MACD - 使用安全的 calculate_ema 函數
        try:
            ema_12 = calculate_ema(closes, 12)
            ema_26 = calculate_ema(closes, 26)
            
            # 確保計算結果是純數值而非數組
            if isinstance(ema_12, np.ndarray):
                ema_12 = float(ema_12[-1])
            if isinstance(ema_26, np.ndarray):
                ema_26 = float(ema_26[-1])
            
            macd_line = ema_12 - ema_26
            
            # 使用列表而非純量進行 EMA 計算
            macd_values = np.zeros(9)
            macd_values.fill(macd_line)
            signal_line = calculate_ema(macd_values, 9)
            
            macd_histogram = macd_line - signal_line
        except Exception as e:
            print(f"[multi_analysis] ⚠️ MACD 計算錯誤：{e}")
            ema_12 = ema_26 = macd_line = signal_line = macd_histogram = 0
        
        # 3. RSI - 添加更多的安全檢查
        try:
            delta = np.diff(closes)
            up_values = np.array([max(d, 0) for d in delta[-14:]])
            down_values = np.array([abs(min(d, 0)) for d in delta[-14:]])
            
            up_avg = np.mean(up_values) if len(up_values) > 0 else 0
            down_avg = np.mean(down_values) if len(down_values) > 0 else 1e-10
            
            rs = up_avg / down_avg if down_avg > 0 else 999
            rsi = 100 - (100 / (1 + rs))
        except Exception as e:
            print(f"[multi_analysis] ⚠️ RSI 計算錯誤：{e}")
            rsi = 50  # 使用中性值作為默認值
        
        # 4. 成交量變化 - 添加安全檢查
        try:
            if len(volumes) >= 20 and np.mean(volumes[-20:]) > 0:
                avg_vol_5 = np.mean(volumes[-5:])
                avg_vol_20 = np.mean(volumes[-20:])
                vol_change = avg_vol_5 / avg_vol_20
            else:
                vol_change = 1
        except Exception as e:
            print(f"[multi_analysis] ⚠️ 成交量變化計算錯誤：{e}")
            vol_change = 1
        
        # 計算技術面得分
        score = 0
        analysis_points = []
        
        # MA評分 (30分)
        ma_score = 0
        try:
            # 短期均線多頭排列
            if ma_5 > ma_10 > ma_20:
                ma_score += 15
                analysis_points.append("短期均線呈多頭排列")
            # 價格站上主要均線
            if closes[-1] > ma_20:
                ma_score += 10
                analysis_points.append("價格站上20日均線")
            if closes[-1] > ma_60:
                ma_score += 5
                analysis_points.append("價格站上60日均線")
        except Exception as e:
            print(f"[multi_analysis] ⚠️ MA 評分計算錯誤：{e}")
        
        score += ma_score
        
        # MACD評分 (25分) - 添加安全檢查
        macd_score = 0
        try:
            if macd_line > signal_line:
                macd_score += 15
                analysis_points.append("MACD位於信號線上方")
            if macd_line > 0:
                macd_score += 5
                analysis_points.append("MACD位於零軸上方")
            if macd_histogram > 0 and len(closes) > 2:
                prev_histogram = ema_12 - ema_26 - signal_line
                if macd_histogram > prev_histogram:
                    macd_score += 5
                    analysis_points.append("MACD柱狀圖擴張中")
        except Exception as e:
            print(f"[multi_analysis] ⚠️ MACD 評分計算錯誤：{e}")
            
        score += macd_score
        
        # RSI評分 (25分) - 添加安全檢查
        rsi_score = 0
        try:
            if 40 <= rsi <= 70:
                rsi_score += 15
                analysis_points.append(f"RSI={rsi:.1f}處於理想區間")
            elif 30 <= rsi < 40:
                rsi_score += 10
                analysis_points.append(f"RSI={rsi:.1f}接近超賣區間")
            elif 70 < rsi <= 80:
                rsi_score += 5
                analysis_points.append(f"RSI={rsi:.1f}接近超買區間")
        except Exception as e:
            print(f"[multi_analysis] ⚠️ RSI 評分計算錯誤：{e}")
            
        score += rsi_score
        
        # 成交量評分 (20分) - 添加安全檢查
        vol_score = 0
        try:
            if vol_change > 1.5:
                vol_score += 20
                analysis_points.append("成交量明顯放大")
            elif vol_change > 1.2:
                vol_score += 15
                analysis_points.append("成交量溫和增加")
            elif vol_change > 0.8:
                vol_score += 10
                analysis_points.append("成交量穩定")
        except Exception as e:
            print(f"[multi_analysis] ⚠️ 成交量評分計算錯誤：{e}")
            
        score += vol_score
        
        # 生成分析文字
        analysis = "、".join(analysis_points)
        if not analysis:
            analysis = "無明顯技術特徵"
        
        return score, analysis
        
    except Exception as e:
        print(f"[multi_analysis] ⚠️ 技術分析出錯：{e}")
        return 0, f"技術分析失敗: {str(e)}"

def calculate_ema(prices, days):
    """
    計算指數移動平均線，增加更多安全檢查
    """
    try:
        # 確保輸入是 numpy array
        if not isinstance(prices, np.ndarray):
            prices = np.array(prices, dtype=np.float64)
        
        # 檢查數據長度
        if len(prices) < days:
            return np.mean(prices)
        
        # 處理可能的 NaN 值
        prices = np.nan_to_num(prices, nan=np.nanmean(prices))
        
        # 使用更穩健的 EMA 計算方法
        alpha = 2.0 / (days + 1.0)
        ema = np.zeros_like(prices)
        ema[0] = prices[0]  # 初始化第一個值
        
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1.0 - alpha) * ema[i-1]
        
        # 返回最後一個 EMA 值
        return float(ema[-1])  # 明確轉換為 float
    except Exception as e:
        print(f"[multi_analysis] ⚠️ EMA 計算錯誤：{e}")
        return 0.0  # 返回安全的默認值

def analyze_fundamental(stock_code):
    """基本面分析"""
    try:
        # 增加重試機制避免 Too Many Requests 錯誤
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                # 使用現有模組獲取基本面資料
                from modules.data.scraper import get_eps_data
                eps_data = get_eps_data()
                
                # 從 Yahoo Finance 獲取其他基本面數據
                ticker = yf.Ticker(f"{stock_code}.TW")
                info = ticker.info
                
                # 從自有資料獲取 EPS 和股息資料
                stock_eps_data = eps_data.get(stock_code, {})
                eps = stock_eps_data.get('eps', None)
                dividend = stock_eps_data.get('dividend', None)
                
                # 從 Yahoo Finance 獲取本益比、淨值比
                pe_ratio = info.get('trailingPE', None)
                pb_ratio = info.get('priceToBook', None)
                
                # 成功獲取數據，跳出重試循環
                break
                
            except Exception as e:
                if "Too Many Requests" in str(e) and attempt < max_retries - 1:
                    print(f"[multi_analysis] ⚠️ Yahoo Finance 速率限制，等待 {retry_delay} 秒後重試...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 增加等待時間
                else:
                    raise
        
        # 計算基本面得分
        score = 0
        analysis_points = []
        
        # EPS評分 (20分)
        if eps is not None:
            if eps > 5:
                score += 20
                analysis_points.append(f"每股盈餘{eps}元，表現優異")
            elif eps > 2:
                score += 15
                analysis_points.append(f"每股盈餘{eps}元，表現良好")
            elif eps > 0:
                score += 10
                analysis_points.append(f"每股盈餘{eps}元，表現一般")
            else:
                analysis_points.append(f"每股盈餘{eps}元，表現不佳")
        
        # 股息殖利率評分 (20分)
        if dividend is not None:
            if dividend > 5:
                score += 20
                analysis_points.append(f"殖利率{dividend}%，股息收益豐厚")
            elif dividend > 3:
                score += 15
                analysis_points.append(f"殖利率{dividend}%，股息收益不錯")
            elif dividend > 1:
                score += 10
                analysis_points.append(f"殖利率{dividend}%，股息收益一般")
            else:
                analysis_points.append(f"殖利率{dividend}%，股息收益較低")
        
        # 本益比評分 (30分)
        if pe_ratio is not None and pe_ratio > 0:
            if 0 < pe_ratio < 10:
                score += 30
                analysis_points.append(f"本益比{pe_ratio:.1f}，估值具吸引力")
            elif 10 <= pe_ratio < 15:
                score += 20
                analysis_points.append(f"本益比{pe_ratio:.1f}，估值合理")
            elif 15 <= pe_ratio < 20:
                score += 10
                analysis_points.append(f"本益比{pe_ratio:.1f}，估值略高")
            else:
                analysis_points.append(f"本益比{pe_ratio:.1f}，估值偏高")
        
        # 淨值比評分 (30分)
        if pb_ratio is not None and pb_ratio > 0:
            if 0 < pb_ratio < 1:
                score += 30
                analysis_points.append(f"淨值比{pb_ratio:.1f}，低於帳面價值")
            elif 1 <= pb_ratio < 2:
                score += 20
                analysis_points.append(f"淨值比{pb_ratio:.1f}，接近帳面價值")
            elif 2 <= pb_ratio < 3:
                score += 10
                analysis_points.append(f"淨值比{pb_ratio:.1f}，高於帳面價值")
            else:
                analysis_points.append(f"淨值比{pb_ratio:.1f}，顯著高於帳面價值")
                
        # 生成分析文字
        analysis = "、".join(analysis_points)
        if not analysis:
            analysis = "無基本面資料"
        
        return score, analysis
        
    except Exception as e:
        print(f"[multi_analysis] ⚠️ 基本面分析出錯：{e}")
        return 0, f"基本面分析失敗: {str(e)}"

def analyze_industry(stock_code):
    """產業趨勢分析"""
    try:
        # 取得股票產業別
        # 優先使用現有模組
        try:
            from modules.data.scraper import get_all_valid_twse_stocks
            all_stocks = get_all_valid_twse_stocks()
            stock_info = next((s for s in all_stocks if s['stock_id'] == stock_code), None)
            industry = stock_info['industry'] if stock_info else None
        except:
            # 若無法獲取，使用 Yahoo Finance
            ticker = yf.Ticker(f"{stock_code}.TW")
            info = ticker.info
            industry = info.get('sector', None)
        
        if not industry:
            return 50, "無法獲取產業資訊"
        
        # 產業景氣評分（0-100）
        # 這裡使用模擬資料，實際應從財經網站或API獲取
        industry_data = {
            "半導體業": {"score": 85, "trend": "上升", "reason": "需求強勁，AI晶片帶動成長"},
            "電子業": {"score": 70, "trend": "持平", "reason": "供應鏈逐漸回穩"},
            "生技醫療": {"score": 75, "trend": "上升", "reason": "醫療需求持續增長"},
            "金融保險": {"score": 60, "trend": "持平", "reason": "利率環境穩定"},
            "營建業": {"score": 50, "trend": "下降", "reason": "房市交易量下滑"},
            "水泥工業": {"score": 45, "trend": "下降", "reason": "建設需求減緩"},
            "食品工業": {"score": 65, "trend": "持平", "reason": "基本民生需求穩定"},
            "塑膠工業": {"score": 55, "trend": "持平", "reason": "原物料價格波動"}
        }
        
        # 默認值
        default_data = {"score": 50, "trend": "持平", "reason": "無特殊產業動向"}
        
        # 嘗試匹配產業資訊
        matched_industry = None
        for key in industry_data.keys():
            if key in industry:
                matched_industry = key
                break
        
        industry_info = industry_data.get(matched_industry, default_data)
        
        # 計算產業趨勢得分（0-100分）
        score = industry_info["score"]
        
        # 生成分析文字
        if industry_info["trend"] == "上升":
            analysis = f"{industry}產業趨勢向上，{industry_info['reason']}"
        elif industry_info["trend"] == "下降":
            analysis = f"{industry}產業趨勢向下，{industry_info['reason']}"
        else:
            analysis = f"{industry}產業趨勢持平，{industry_info['reason']}"
        
        return score, analysis
        
    except Exception as e:
        print(f"[multi_analysis] ⚠️ 產業分析出錯：{e}")
        return 50, f"產業分析失敗: {str(e)}"

def analyze_market_sentiment(stock_code):
    """市場情緒分析"""
    try:
        # 1. 獲取整體市場情緒
        from modules.analysis.sentiment import get_market_sentiment_score
        market_score = get_market_sentiment_score()
        
        # 2. 獲取個股相對強度
        ticker = yf.Ticker(f"{stock_code}.TW")
        history = ticker.history(period="30d")
        
        if history.empty or len(history) < 20:
            return market_score * 0.8, f"市場整體情緒評分：{market_score}/10"
        
        # 計算個股與大盤的相對表現
        try:
            twii = yf.Ticker("^TWII")  # 台灣加權指數
            twii_history = twii.history(period="30d")
            
            if not twii_history.empty and len(twii_history) >= 20:
                # 計算近20天的表現
                # 修正 FutureWarning 問題
                stock_last = history['Close'].iloc[-1]
                stock_prev = history['Close'].iloc[-20]
                market_last = twii_history['Close'].iloc[-1]
                market_prev = twii_history['Close'].iloc[-20]
                
                # 如果返回的是 Series，取第一個元素
                if isinstance(stock_last, pd.Series):
                    stock_last = stock_last.iloc[0]
                if isinstance(stock_prev, pd.Series):
                    stock_prev = stock_prev.iloc[0]
                if isinstance(market_last, pd.Series):
                    market_last = market_last.iloc[0]
                if isinstance(market_prev, pd.Series):
                    market_prev = market_prev.iloc[0]
                
                stock_change = (stock_last / stock_prev - 1) * 100
                market_change = (market_last / market_prev - 1) * 100
                
                # 相對強度
                relative_strength = stock_change - market_change
            else:
                relative_strength = 0
        except Exception as e:
            print(f"[multi_analysis] ⚠️ 相對強度計算錯誤：{e}")
            relative_strength = 0
        
        # 3. 計算資金流向
        volume_change = 0
        if 'Volume' in history.columns and len(history) >= 10:
            try:
                recent_vol = history['Volume'].tail(5).mean()
                prev_vol = history['Volume'].iloc[-10:-5].mean()
                
                # 如果返回的是 Series，取第一個元素
                if isinstance(recent_vol, pd.Series):
                    recent_vol = recent_vol.iloc[0]
                if isinstance(prev_vol, pd.Series):
                    prev_vol = prev_vol.iloc[0]
                
                if prev_vol > 0:
                    volume_change = (recent_vol / prev_vol - 1) * 100
            except Exception as e:
                print(f"[multi_analysis] ⚠️ 資金流向計算錯誤：{e}")
        
        # 4. 計算情緒得分 (0-100)
        sentiment_score = min(100, max(0, market_score * 10))  # 市場情緒 (0-100)
        
        # 根據相對強度調整
        if relative_strength > 5:  # 明顯強於大盤
            sentiment_score += 20
            rs_text = f"個股強於大盤 {relative_strength:.1f}%"
        elif relative_strength > 0:  # 略強於大盤
            sentiment_score += 10
            rs_text = f"個股略強於大盤 {relative_strength:.1f}%"
        elif relative_strength < -5:  # 明顯弱於大盤
            sentiment_score -= 20
            rs_text = f"個股弱於大盤 {abs(relative_strength):.1f}%"
        elif relative_strength < 0:  # 略弱於大盤
            sentiment_score -= 10
            rs_text = f"個股略弱於大盤 {abs(relative_strength):.1f}%"
        else:
            rs_text = "個股表現與大盤相當"
        
        # 根據資金流向調整
        if volume_change > 30:  # 資金大幅流入
            sentiment_score += 20
            vol_text = f"資金大幅流入 (成交量增加 {volume_change:.1f}%)"
        elif volume_change > 10:  # 資金流入
            sentiment_score += 10
            vol_text = f"資金小幅流入 (成交量增加 {volume_change:.1f}%)"
        elif volume_change < -30:  # 資金大幅流出
            sentiment_score -= 20
            vol_text = f"資金大幅流出 (成交量減少 {abs(volume_change):.1f}%)"
        elif volume_change < -10:  # 資金流出
            sentiment_score -= 10
            vol_text = f"資金小幅流出 (成交量減少 {abs(volume_change):.1f}%)"
        else:
            vol_text = "資金流向維持平衡"
        
        # 限制分數範圍
        sentiment_score = min(100, max(0, sentiment_score))
        
        # 生成分析文字
        analysis = f"市場整體情緒：{market_score}/10，{rs_text}，{vol_text}"
        
        return sentiment_score, analysis
        
    except Exception as e:
        print(f"[multi_analysis] ⚠️ 市場情緒分析出錯：{e}")
        # 如果出錯，返回較中性的評分
        return 50, f"市場情緒分析失敗: {str(e)}"
