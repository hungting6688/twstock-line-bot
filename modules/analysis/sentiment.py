"""
市場情緒分析模組 - 整合 market_sentiment.py
"""
print("[sentiment] ✅ 已載入最新版")

import yfinance as yf
from datetime import datetime, timedelta


def get_market_sentiment_score():
    """
    獲取整體市場情緒評分
    
    返回:
    - 市場情緒評分 (0-10)
    """
    # 監控的主要指數
    indices = {
        "^TWII": "台股加權",
        "^N225": "日經",
        "^HSI": "恆生",
        "^GSPC": "標普500",
        "^IXIC": "那斯達克",
    }

    today = datetime.today()
    start_date = today - timedelta(days=5)

    score = 0
    max_score = len(indices) * 2  # 每個指數最高可得2分

    # 分析每個指數的漲跌
    for symbol, name in indices.items():
        try:
            df = yf.download(symbol, start=start_date.strftime('%Y-%m-%d'), end=today.strftime('%Y-%m-%d'), progress=False)
            closes = df["Close"].dropna()
            
            if len(closes) < 2:
                raise ValueError("資料不足")
                
            last_close = float(closes.iloc[-1].iloc[0]) if isinstance(closes.iloc[-1], pd.Series) else float(closes.iloc[-1])
            prev_close = float(closes.iloc[-2].iloc[0]) if isinstance(closes.iloc[-2], pd.Series) else float(closes.iloc[-2])
            pct_change = (last_close - prev_close) / prev_close

            # 根據漲跌幅度給分
            if pct_change > 0.01:  # 漲幅超過1%
                score += 2
            elif pct_change > 0:   # 小幅上漲
                score += 1

        except Exception as e:
            print(f"[sentiment] ❌ 無法讀取 {symbol}：{e}")
            continue

    # 轉換為0-10的評分
    normalized_score = round((score / max_score) * 10, 1)
    print(f"[sentiment] ✅ 市場情緒評分：{normalized_score}/10")
    
    return normalized_score


def get_market_sentiment_adjustments():
    """
    根據市場情緒提供各指標的權重調整
    
    返回:
    - 權重調整系數字典
    """
    # 獲取當前市場情緒評分
    score = get_market_sentiment_score()

    # 根據情緒分數提供不同的權重調整
    if score >= 8:  # 非常樂觀
        return {
            "MACD": 1.2,   # 強化短期趨勢指標
            "KD": 1.2,
            "RSI": 1.1,
            "MA": 1.2,
            "BB": 1.1,
            "dividend": 1.0,  # 不調整股息指標
            "eps": 1.0,
            "pe": 0.9,     # 弱化估值指標
            "roe": 0.9,
        }
    elif score >= 5:  # 中性
        return {
            "MACD": 1.0,
            "KD": 1.0,
            "RSI": 1.0,
            "MA": 1.0,
            "BB": 1.0,
            "dividend": 1.0,
            "eps": 1.0,
            "pe": 1.0,
            "roe": 1.0,
        }
    else:  # 悲觀
        return {
            "MACD": 0.8,   # 弱化趨勢指標
            "KD": 0.9,
            "RSI": 0.9,
            "MA": 0.8,
            "BB": 0.9,
            "dividend": 1.2,  # 強化價值指標
            "eps": 1.2,
            "pe": 1.1,
            "roe": 1.1,
        }


def analyze_relative_strength(stock_code):
    """
    分析個股相對於大盤的強弱
    
    參數:
    - stock_code: 股票代碼
    
    返回:
    - 相對強度 (百分比), 強度描述
    """
    try:
        # 取得最近20天的股價數據
        ticker = yf.Ticker(f"{stock_code}.TW")
        history = ticker.history(period="30d")
        
        if history.empty or len(history) < 20:
            return 0, "資料不足無法分析相對強度"
            
        # 取得同期台股加權指數數據
        twii = yf.Ticker("^TWII")
        twii_history = twii.history(period="30d")
        
        if twii_history.empty or len(twii_history) < 20:
            return 0, "無法取得台股加權指數數據"
            
        # 計算漲跌幅
        stock_change = (history['Close'].iloc[-1] / history['Close'].iloc[-20] - 1) * 100
        market_change = (twii_history['Close'].iloc[-1] / twii_history['Close'].iloc[-20] - 1) * 100
        
        # 計算相對強度
        relative_strength = stock_change - market_change
        
        # 生成描述
        if relative_strength > 5:
            desc = f"強勢：超越大盤 {relative_strength:.1f}%"
        elif relative_strength > 0:
            desc = f"略強：優於大盤 {relative_strength:.1f}%"
        elif relative_strength > -5:
            desc = f"略弱：低於大盤 {abs(relative_strength):.1f}%"
        else:
            desc = f"弱勢：明顯落後大盤 {abs(relative_strength):.1f}%"
            
        return relative_strength, desc
        
    except Exception as e:
        print(f"[sentiment] ⚠️ {stock_code} 相對強度分析失敗：{e}")
        return 0, "無法分析相對強度"


def analyze_fund_flow(stock_code, days=5):
    """
    分析個股資金流向
    
    參數:
    - stock_code: 股票代碼
    - days: 分析天數
    
    返回:
    - 資金流向強度, 流向描述
    """
    try:
        ticker = yf.Ticker(f"{stock_code}.TW")
        history = ticker.history(period="30d")
        
        if history.empty or len(history) < days + 5:
            return 0, "資料不足無法分析資金流向"
            
        # 確認成交量欄位存在
        if 'Volume' not in history.columns:
            return 0, "無成交量資料"
            
        # 計算最近幾天和之前幾天的平均成交量
        recent_vol = history['Volume'].tail(days).mean()
        prev_vol = history['Volume'].iloc[-2*days:-days].mean()
        
        if prev_vol == 0:
            return 0, "無法計算成交量變化"
            
        # 計算成交量變化比例
        volume_change = (recent_vol / prev_vol - 1) * 100
        
        # 生成描述
        if volume_change > 30:
            desc = f"資金大幅流入 (成交量增加 {volume_change:.1f}%)"
            strength = 2
        elif volume_change > 10:
            desc = f"資金小幅流入 (成交量增加 {volume_change:.1f}%)"
            strength = 1
        elif volume_change > -10:
            desc = "資金流向維持平衡"
            strength = 0
        elif volume_change > -30:
            desc = f"資金小幅流出 (成交量減少 {abs(volume_change):.1f}%)"
            strength = -1
        else:
            desc = f"資金大幅流出 (成交量減少 {abs(volume_change):.1f}%)"
            strength = -2
            
        return strength, desc
        
    except Exception as e:
        print(f"[sentiment] ⚠️ {stock_code} 資金流向分析失敗：{e}")
        return 0, "無法分析資金流向"
