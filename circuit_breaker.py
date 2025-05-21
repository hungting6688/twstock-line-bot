"""
circuit_breaker.py - 熔斷機制實現
"""
import time
import json
import os
import logging
from datetime import datetime

# 確保日誌目錄存在
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)

# 配置日誌
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'circuit_breaker.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CircuitBreaker:
    """
    熔斷器實現 - 防止持續請求已知失敗的服務
    """
    
    # 靜態熔斷器實例集合，確保全局一致性
    _instances = {}
    
    # 熔斷器持久化文件路徑
    _state_file = os.path.join(LOG_DIR, 'circuit_breakers.json')
    
    @staticmethod
    def get_instance(name):
        """
        獲取指定名稱的熔斷器實例
        
        參數:
        - name: 熔斷器名稱
        
        返回:
        - CircuitBreaker: 熔斷器實例
        """
        if name not in CircuitBreaker._instances:
            CircuitBreaker._instances[name] = CircuitBreaker(name)
        return CircuitBreaker._instances[name]
        
    def __init__(self, name, failure_threshold=5, reset_timeout=300, half_open_max_calls=3):
        """
        初始化熔斷器
        
        參數:
        - name: 熔斷器名稱
        - failure_threshold: 失敗閾值，達到此值後將開啟熔斷
        - reset_timeout: 重置超時時間(秒)，經過此時間後嘗試半開狀態
        - half_open_max_calls: 半開狀態下允許的最大調用次數
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls
        
        # 狀態變量
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = time.time()
        self.half_open_calls = 0
        
        # 嘗試從持久化存儲加載狀態
        self._load_state()
        
    def record_success(self):
        """記錄成功操作"""
        self.success_count += 1
        self.failure_count = max(0, self.failure_count - 1)  # 遞減失敗計數
        
        if self.state == "HALF-OPEN":
            self.half_open_calls += 1
            
            # 如果半開狀態下成功達到閾值，關閉熔斷器
            if self.success_count >= self.half_open_max_calls:
                self._change_state("CLOSED")
                
        self._save_state()
        
    def record_failure(self):
        """記錄失敗操作"""
        self.failure_count += 1
        self.success_count = 0  # 重置成功計數
        self.last_failure_time = time.time()
        
        if self.state == "CLOSED" and self.failure_count >= self.failure_threshold:
            self._change_state("OPEN")
            
        elif self.state == "HALF-OPEN":
            # 半開狀態下的失敗立即重新開啟熔斷器
            self._change_state("OPEN")
            
        self._save_state()
        
    def allow_request(self):
        """
        檢查是否允許請求
        
        返回:
        - bool: 是否允許請求
        """
        current_time = time.time()
        
        if self.state == "CLOSED":
            return True
        
        if self.state == "OPEN":
            # 檢查是否應該嘗試半開狀態
            if self.last_failure_time and current_time - self.last_failure_time > self.reset_timeout:
                self._change_state("HALF-OPEN")
                return True
            return False
            
        if self.state == "HALF-OPEN":
            # 半開狀態限制調用次數
            return self.half_open_calls < self.half_open_max_calls
            
        return True  # 默認允許
        
    def get_state(self):
        """
        獲取熔斷器詳細狀態
        
        返回:
        - dict: 熔斷器狀態詳情
        """
        current_time = time.time()
        
        state_info = {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "reset_timeout": self.reset_timeout
        }
        
        if self.last_failure_time:
            state_info["last_failure"] = datetime.fromtimestamp(self.last_failure_time).isoformat()
            state_info["time_since_failure"] = round(current_time - self.last_failure_time, 1)
            
            if self.state == "OPEN":
                remaining = self.reset_timeout - (current_time - self.last_failure_time)
                if remaining > 0:
                    state_info["remaining_timeout"] = round(remaining, 1)
        
        if self.state == "HALF-OPEN":
            state_info["half_open_calls"] = self.half_open_calls
            state_info["half_open_max_calls"] = self.half_open_max_calls
            
        return state_info
    
    def reset(self):
        """重置熔斷器到初始狀態"""
        self._change_state("CLOSED")
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        self._save_state()
        
    def _change_state(self, new_state):
        """
        改變熔斷器狀態
        
        參數:
        - new_state: 新狀態
        """
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            self.last_state_change = time.time()
            self.half_open_calls = 0
            
            # 記錄狀態變化
            msg = f"熔斷器 '{self.name}' 狀態從 {old_state} 變為 {new_state}"
            print(f"[circuit_breaker] {msg}")
            logging.info(msg)
            
            # 特定狀態的額外動作
            if new_state == "OPEN":
                logging.warning(f"熔斷器 '{self.name}' 已開啟，失敗計數: {self.failure_count}")
            elif new_state == "CLOSED":
                logging.info(f"熔斷器 '{self.name}' 已關閉，服務恢復正常")
    
    def _save_state(self):
        """保存熔斷器狀態到持久化存儲"""
        try:
            # 讀取現有狀態
            all_states = {}
            if os.path.exists(self._state_file):
                with open(self._state_file, 'r', encoding='utf-8') as f:
                    all_states = json.load(f)
            
            # 更新當前熔斷器狀態
            all_states[self.name] = {
                "state": self.state,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure_time": self.last_failure_time,
                "last_state_change": self.last_state_change,
                "half_open_calls": self.half_open_calls,
                "updated_at": time.time()
            }
            
            # 寫回文件
            with open(self._state_file, 'w', encoding='utf-8') as f:
                json.dump(all_states, f, indent=2)
                
        except Exception as e:
            logging.error(f"保存熔斷器狀態失敗: {e}")
    
    def _load_state(self):
        """從持久化存儲加載熔斷器狀態"""
        try:
            if not os.path.exists(self._state_file):
                return
                
            with open(self._state_file, 'r', encoding='utf-8') as f:
                all_states = json.load(f)
                
            if self.name in all_states:
                state_data = all_states[self.name]
                
                # 更新狀態變量
                self.state = state_data.get("state", "CLOSED")
                self.failure_count = state_data.get("failure_count", 0)
                self.success_count = state_data.get("success_count", 0)
                self.last_failure_time = state_data.get("last_failure_time")
                self.last_state_change = state_data.get("last_state_change", time.time())
                self.half_open_calls = state_data.get("half_open_calls", 0)
                
                # 處理重啟後的熔斷器狀態
                if self.state == "HALF-OPEN":
                    # 半開狀態下重啟，重置為開啟
                    self._change_state("OPEN")
                elif self.state == "OPEN":
                    # 檢查開啟狀態是否已超時
                    if self.last_failure_time and time.time() - self.last_failure_time > self.reset_timeout:
                        self._change_state("HALF-OPEN")
                
        except Exception as e:
            logging.error(f"加載熔斷器狀態失敗: {e}")
            # 默認使用關閉狀態
            self.state = "CLOSED"

    @staticmethod
    def get_all_states():
        """
        獲取所有熔斷器的狀態
        
        返回:
        - dict: 所有熔斷器狀態
        """
        results = {}
        for name, instance in CircuitBreaker._instances.items():
            results[name] = instance.get_state()
        return results

    @staticmethod
    def reset_all():
        """重置所有熔斷器"""
        for instance in CircuitBreaker._instances.values():
            instance.reset()
        
        # 清除持久化文件
        if os.path.exists(CircuitBreaker._state_file):
            os.remove(CircuitBreaker._state_file)
            logging.info("所有熔斷器已重置")
