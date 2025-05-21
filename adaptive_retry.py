"""
adaptive_retry.py - 自適應重試策略
"""
import logging
import time
import json
import os
import random
from datetime import datetime
from error_category import ErrorCategory

# 確保日誌目錄存在
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 配置日誌
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'adaptive_retry.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class AdaptiveRetry:
    """自適應重試策略"""
    
    # 所有實例的字典
    _instances = {}
    
    # 持久化文件
    _history_file = os.path.join(LOG_DIR, 'retry_history.json')
    
    @staticmethod
    def get_instance(service_name):
        """
        獲取指定服務的實例
        
        參數:
        - service_name: 服務名稱
        
        返回:
        - AdaptiveRetry: 實例
        """
        if service_name not in AdaptiveRetry._instances:
            AdaptiveRetry._instances[service_name] = AdaptiveRetry(service_name)
        return AdaptiveRetry._instances[service_name]
    
    def __init__(self, service_name, window_size=100, min_attempts=1, max_attempts=5):
        """
        初始化自適應重試策略
        
        參數:
        - service_name: 服務名稱
        - window_size: 歷史窗口大小
        - min_attempts: 最小嘗試次數
        - max_attempts: 最大嘗試次數
        """
        self.service_name = service_name
        self.window_size = window_size
        self.min_attempts = min_attempts
        self.max_attempts = max_attempts
        
        self.attempts_history = []  # 歷史嘗試次數與結果的記錄
        # [{'timestamp', 'attempts', 'success', 'error_type', 'duration'}]
        
        self.current_max_attempts = 3  # 初始設置
        self.last_adaptation_time = None
        self.adaptation_interval = 3600  # 每小時調整一次
        
        # 嘗試加載歷史數據
        self._load_history()
    
    def record_result(self, attempts, success, error_type=None, duration=None):
        """
        記錄一次嘗試結果
        
        參數:
        - attempts: 嘗試次數
        - success: 是否成功
        - error_type: 錯誤類型 (可選)
        - duration: 持續時間(秒) (可選)
        """
        # 記錄結果
        record = {
            'timestamp': datetime.now().isoformat(),
            'attempts': attempts,
            'success': success,
            'error_type': error_type,
            'duration': duration
        }
        
        # 添加到歷史記錄
        self.attempts_history.append(record)
        
        # 保持窗口大小
        if len(self.attempts_history) > self.window_size:
            self.attempts_history = self.attempts_history[-self.window_size:]
        
        # 檢查是否應該調整
        now = time.time()
        if (self.last_adaptation_time is None or 
            now - self.last_adaptation_time > self.adaptation_interval):
            # 動態調整最大嘗試次數
            self._adapt_max_attempts()
            self.last_adaptation_time = now
        
        # 保存歷史數據
        self._save_history()
    
    def get_max_attempts(self, error_type=None):
        """
        獲取當前最大嘗試次數
        
        參數:
        - error_type: 錯誤類型，None表示使用自適應值
        
        返回:
        - int: 最大嘗試次數
        """
        # 如果指定了錯誤類型，優先使用錯誤類型的建議值
        if error_type:
            error_max_attempts = ErrorCategory.get_max_attempts(error_type)
            # 如果錯誤類型的嘗試次數小於自適應值，使用錯誤類型的值
            if error_max_attempts < self.current_max_attempts:
                return error_max_attempts
        
        return self.current_max_attempts
    
    def calculate_delay(self, attempt, error_type=None):
        """
        計算重試延遲時間
        
        參數:
        - attempt: 當前嘗試次數
        - error_type: 錯誤類型 (可選)
        
        返回:
        - float: 延遲時間(秒)
        """
        # 從錯誤類型獲取策略
        strategy = None
        if error_type:
            strategy = ErrorCategory.get_strategy(error_type)
        
        # 使用默認策略
        if not strategy:
            base_delay = 2.0
            backoff_factor = 2.0
            jitter = 0.5
            max_delay = 60.0
        else:
            base_delay = strategy.get('base_delay', 2.0)
            backoff_factor = strategy.get('backoff_factor', 2.0)
            jitter = 0.5
            max_delay = 60.0
        
        # 計算指數退避延遲
        delay = base_delay * (backoff_factor ** (attempt - 1))
        # 加入隨機抖動
        delay = delay * (1 + random.uniform(-jitter, jitter))
        # 限制最大延遲
        delay = min(delay, max_delay)
        
        return delay
    
    def _adapt_max_attempts(self):
        """適應性調整最大嘗試次數"""
        # 如果樣本太少，不調整
        if len(self.attempts_history) < 10:
            return
        
        # 分析每次嘗試的成功率
        success_by_attempt = {}
        for attempt in range(1, self.max_attempts + 1):
            # 找出嘗試次數等於 attempt 的成功次數
            success_records = [
                record for record in self.attempts_history 
                if record['success'] and record['attempts'] == attempt
            ]
            
            # 找出至少嘗試了 attempt 次的記錄總數
            total_records = [
                record for record in self.attempts_history 
                if record['attempts'] >= attempt
            ]
            
            if total_records:
                success_by_attempt[attempt] = len(success_records) / len(total_records)
            else:
                success_by_attempt[attempt] = 0
        
        logging.info(f"服務 {self.service_name} 成功率分析: {success_by_attempt}")
        
        # 找出邊際收益變低的嘗試次數
        new_max_attempts = self.min_attempts
        for attempt in range(self.min_attempts + 1, self.max_attempts + 1):
            # 計算邊際收益 (第 attempt 次嘗試的成功率)
            marginal_benefit = success_by_attempt.get(attempt, 0)
            
            # 如果邊際收益低於閾值，不再增加嘗試次數
            if marginal_benefit < 0.05:  # 5%的邊際收益閾值
                break
                
            new_max_attempts = attempt
        
        # 更新最大嘗試次數
        old_max = self.current_max_attempts
        self.current_max_attempts = new_max_attempts
        
        logging.info(f"服務 {self.service_name} 最大嘗試次數從 {old_max} 調整為 {new_max_attempts}")
    
    def get_success_rate(self):
        """
        獲取總體成功率
        
        返回:
        - float: 成功率 (0-1)
        """
        if not self.attempts_history:
            return 0
            
        success_count = sum(1 for record in self.attempts_history if record['success'])
        return success_count / len(self.attempts_history)
    
    def get_average_attempts(self):
        """
        獲取平均嘗試次數
        
        返回:
        - float: 平均嘗試次數
        """
        if not self.attempts_history:
            return 0
            
        total_attempts = sum(record['attempts'] for record in self.attempts_history)
        return total_attempts / len(self.attempts_history)
    
    def get_stats(self):
        """
        獲取統計數據
        
        返回:
        - dict: 統計數據
        """
        if not self.attempts_history:
            return {
                'service_name': self.service_name,
                'current_max_attempts': self.current_max_attempts,
                'success_rate': 0,
                'average_attempts': 0,
                'total_records': 0,
                'success_by_attempt': {},
                'last_adaptation': self.last_adaptation_time
            }
        
        # 計算成功率
        success_count = sum(1 for record in self.attempts_history if record['success'])
        success_rate = success_count / len(self.attempts_history)
        
        # 計算平均嘗試次數
        total_attempts = sum(record['attempts'] for record in self.attempts_history)
        average_attempts = total_attempts / len(self.attempts_history)
        
        # 計算每次嘗試的成功率
        success_by_attempt = {}
        for attempt in range(1, self.max_attempts + 1):
            # 找出嘗試次數等於 attempt 的成功次數
            success_records = [
                record for record in self.attempts_history 
                if record['success'] and record['attempts'] == attempt
            ]
            
            # 找出至少嘗試了 attempt 次的記錄總數
            total_records = [
                record for record in self.attempts_history 
                if record['attempts'] >= attempt
            ]
            
            if total_records:
                success_by_attempt[str(attempt)] = len(success_records) / len(total_records)
            else:
                success_by_attempt[str(attempt)] = 0
        
        # 按錯誤類型統計
        error_types = {}
        for record in self.attempts_history:
            if not record['success'] and record['error_type']:
                error_type = record['error_type']
                if error_type not in error_types:
                    error_types[error_type] = 0
                error_types[error_type] += 1
        
        return {
            'service_name': self.service_name,
            'current_max_attempts': self.current_max_attempts,
            'success_rate': success_rate,
            'average_attempts': average_attempts,
            'total_records': len(self.attempts_history),
            'success_by_attempt': success_by_attempt,
            'error_types': error_types,
            'last_adaptation': self.last_adaptation_time
        }
    
    def _save_history(self):
        """保存歷史數據"""
        try:
            # 讀取現有數據
            all_history = {}
            if os.path.exists(self._history_file):
                with open(self._history_file, 'r', encoding='utf-8') as f:
                    all_history = json.load(f)
            
            # 更新當前服務的歷史
            all_history[self.service_name] = {
                'attempts_history': self.attempts_history,
                'current_max_attempts': self.current_max_attempts,
                'last_adaptation_time': self.last_adaptation_time,
                'updated_at': datetime.now().isoformat()
            }
            
            # 寫回文件
            with open(self._history_file, 'w', encoding='utf-8') as f:
                json.dump(all_history, f, indent=2)
                
        except Exception as e:
            logging.error(f"保存重試歷史數據失敗: {e}")
    
    def _load_history(self):
        """加載歷史數據"""
        try:
            if not os.path.exists(self._history_file):
                return
                
            with open(self._history_file, 'r', encoding='utf-8') as f:
                all_history = json.load(f)
                
            if self.service_name in all_history:
                service_history = all_history[self.service_name]
                
                # 載入歷史記錄
                self.attempts_history = service_history.get('attempts_history', [])
                
                # 載入最大嘗試次數
                self.current_max_attempts = service_history.get('current_max_attempts', 3)
                
                # 載入上次調整時間
                last_time = service_history.get('last_adaptation_time')
                if last_time:
                    self.last_adaptation_time = last_time
                
                logging.info(f"加載了 {self.service_name} 的 {len(self.attempts_history)} 條歷史數據")
                
      except Exception as e:
            logging.error(f"加載重試歷史數據失敗: {e}")
def retry(self, func, *args, error_types=None, **kwargs):
    """
    使用自適應重試策略執行函數
    
    參數:
    - func: 要執行的函數
    - *args: 函數參數
    - error_types: 可重試的錯誤類型列表
    - **kwargs: 函數關鍵字參數
    
    返回:
    - 函數執行結果
    
    異常:
    - 超過最大重試次數後仍失敗
    """
    start_time = time.time()
    error_type = None
    attempt = 0
    last_error = None
    
    max_attempts = self.get_max_attempts()
    
    while attempt < max_attempts:
        attempt += 1
        
        try:
            # 執行目標函數
            result = func(*args, **kwargs)
            
            # 計算持續時間
            duration = time.time() - start_time
            
            # 記錄成功
            self.record_result(attempts=attempt, success=True, duration=duration)
            
            # 返回結果
            return result
            
        except Exception as e:
            last_error = e
            
            # 檢查是否為可重試的錯誤
            if error_types and not any(isinstance(e, t) for t in error_types):
                # 不可重試的錯誤類型，直接拋出
                raise
            
            # 識別錯誤類型
            error_type = ErrorCategory.categorize_error(e)
            
            # 檢查是否應該繼續重試
            if attempt >= self.get_max_attempts(error_type):
                break
            
            # 計算延遲時間
            delay = self.calculate_delay(attempt, error_type)
            
            # 記錄重試
            logging.info(
                f"服務 {self.service_name} 第 {attempt} 次嘗試失敗，"
                f"錯誤類型: {error_type}，將在 {delay:.2f} 秒後重試。"
                f"錯誤: {str(e)}"
            )
            
            # 等待延遲時間
            time.sleep(delay)
    
    # 記錄最終失敗
    duration = time.time() - start_time
    self.record_result(
        attempts=attempt, 
        success=False, 
        error_type=error_type, 
        duration=duration
    )
    
    # 拋出最後一個錯誤
    logging.error(
        f"服務 {self.service_name} 在 {attempt} 次嘗試後仍然失敗。"
        f"最後錯誤: {str(last_error)}"
    )
    raise last_error


@staticmethod
def reset_all_history():
    """重置所有服務的歷史數據"""
    try:
        if os.path.exists(AdaptiveRetry._history_file):
            os.remove(AdaptiveRetry._history_file)
        AdaptiveRetry._instances = {}
        logging.info("已重置所有服務的重試歷史數據")
    except Exception as e:
        logging.error(f"重置重試歷史數據失敗: {e}")


@staticmethod
def get_all_services_stats():
    """獲取所有服務的統計數據"""
    stats = {}
    for service_name, instance in AdaptiveRetry._instances.items():
        stats[service_name] = instance.get_stats()
    return stats


def reset_history(self):
    """重置當前服務的歷史數據"""
    self.attempts_history = []
    self.current_max_attempts = 3
    self.last_adaptation_time = None
    
    # 更新保存的歷史數據
    self._save_history()
    logging.info(f"已重置服務 {self.service_name} 的重試歷史數據")


# 方便使用的裝飾器
def with_retry(service_name, error_types=None):
    """
    自適應重試裝飾器
    
    參數:
    - service_name: 服務名稱
    - error_types: 可重試的錯誤類型列表
    
    返回:
    - 裝飾器函數
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 獲取重試實例
            retry_instance = AdaptiveRetry.get_instance(service_name)
            
            # 使用重試策略執行函數
            return retry_instance.retry(func, *args, error_types=error_types, **kwargs)
        
        return wrapper
    
    return decorator
