#!/usr/bin/env python3
"""
股票財報數據功能測試腳本 (改進版)
用於測試 EPS 和股息數據獲取功能
"""

import os
import sys
import time
import pandas as pd
from datetime import datetime

def test_original_eps_fetcher():
    """測試原始 EPS 數據獲取方法"""
    print("\n[測試] 開始測試原始 EPS 數據獲取方法...")
    
    try:
        # 直接導入原始函數進行測試
        from modules.data.scraper import get_eps_data
        
        print("[測試] 調用原始 get_eps_data() 函數...")
        start_time = time.time()
        eps_data = get_eps_data()
        end_time = time.time()
        
        if not eps_data:
            print("[測試] ❌ 原始方法無法獲取 EPS 數據")
            return False
        
        # 顯示取得的數據
        count = 0
        print("[測試] 原始方法獲取的 EPS 數據樣本:")
        for stock_id, data in eps_data.items():
            print(f"  股票代號: {stock_id}, EPS: {data.get('eps')}, 股息: {data.get('dividend')}")
            count += 1
            if count >= 5:
                break
        
        print(f"[測試] ✅ 原始方法成功獲取 EPS 數據，共 {len(eps_data)} 檔股票")
        print(f"[測試] 耗時: {end_time - start_time:.2f} 秒")
        return True
    
    except Exception as e:
        print(f"[測試] ❌ 原始方法獲取 EPS 數據失敗: {e}")
        return False


def test_yahoo_finance_data():
    """測試使用 Yahoo Finance 獲取財務數據"""
    print("\n[測試] 開始測試 Yahoo Finance 替代方案...")
    
    try:
        # 導入 Yahoo Finance 替代方案
        import yfinance as yf
        from modules.data.scraper import get_all_valid_twse_stocks
        
        # 測試獲取幾檔知名股票的數據
        print("[測試] 從 Yahoo Finance 獲取測試股票數據...")
        test_stocks = ["2330", "2317", "2454", "2882", "2412"]
        
        results = {}
        success_count = 0
        
        start_time = time.time()
        for stock_id in test_stocks:
            try:
                print(f"[測試] 正在處理 {stock_id}...")
                ticker = yf.Ticker(f"{stock_id}.TW")
                info = ticker.info
                
                # 獲取 EPS
                eps = info.get('trailingEPS')
                if eps and eps != 'N/A':
                    eps = round(float(eps), 2)
                
                # 獲取股息率
                dividend_yield = info.get('dividendYield', 0)
                if dividend_yield:
                    dividend_yield = round(dividend_yield * 100, 2)
                
                results[stock_id] = {
                    "eps": eps,
                    "dividend": dividend_yield if dividend_yield > 0 else None
                }
                
                success_count += 1
                print(f"[測試] ✓ {stock_id} 處理成功")
            
            except Exception as e:
                print(f"[測試] ✗ {stock_id} 處理失敗: {e}")
        
        end_time = time.time()
        
        # 顯示結果
        print("\n[測試] Yahoo Finance 數據獲取結果:")
        for stock_id, data in results.items():
            print(f"  股票代號: {stock_id}, EPS: {data['eps']}, 股息率: {data['dividend']}%")
        
        print(f"[測試] 成功率: {success_count}/{len(test_stocks)}")
        print(f"[測試] 耗時: {end_time - start_time:.2f} 秒")
        
        return success_count > 0
    
    except Exception as e:
        print(f"[測試] ❌ Yahoo Finance 測試失敗: {e}")
        return False


def run_focused_tests():
    """執行針對財報數據的聚焦測試"""
    print("=" * 60)
    print(f"財報數據獲取測試開始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("原始 EPS 獲取方法", test_original_eps_fetcher),
        ("Yahoo Finance 替代方案", test_yahoo_finance_data)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{'-' * 50}")
        print(f"執行 {name}...")
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"[測試] ❌ 測試過程出錯: {e}")
            results.append((name, False))
    
    # 顯示總結果
    print("\n" + "=" * 60)
    print("財報數據測試結果總結:")
    all_success = True
    for name, success in results:
        status = "✅ 成功" if success else "❌ 失敗"
        all_success = all_success and success
        print(f"  {name}: {status}")
    
    if all_success:
        print("\n所有測試通過! 可以使用這些方法獲取財報數據。")
    else:
        print("\n有些測試失敗。建議使用通過測試的方法來獲取財報數據。")
    
    return all_success


if __name__ == "__main__":
    run_focused_tests()
