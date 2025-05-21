"""
modules/data/connection_manager.py
網路連接管理模組 - 處理重試、錯誤和速率限制
"""
import os
import time
import random
import requests
import socket
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
from datetime import datetime

# 確保日誌目錄存在
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# 增加隨機化的 User-Agent 列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
]

# 常用域名與其IP映射 (可手動更新)
DOMAIN_IP_MAPPING = {
    "finance.yahoo.com": "74.6.231.20",
    "query1.finance.yahoo.com": "74.6.231.20",
    "query2.finance.yahoo.com": "74.6.231.20",
    "mops.twse.com.tw": "210.241.81.171",
    "www.twse.com.tw": "168.95.190.105",
    "isin.twse.com.tw": "210.241.81.172"
}

# 連接問題計數器和黑名單
CONNECTION_STATS = {
    'yahoo_finance': {'failures': 0, 'last_success': None, 'rate_limited_until': None},
    'mops': {'failures': 0, 'last_success': None, 'rate_limited_until': None},
    'twse': {'failures': 0, 'last_success': None, 'rate_limited_until': None}
}

def get_random_user_agent():
    """返回隨機的 User-Agent"""
    return random.choice(USER_AGENTS)

def create_robust_session(retries=3, backoff_factor=0.5, 
                        status_forcelist=(500, 502, 504, 429),
                        allowed_methods=('GET', 'POST'),
                        timeout=(15, 30)):
    """
    建立一個具有強健連接處理的 requests session
    
    參數:
    - retries: 重試次數
    - backoff_factor: 重試延遲倍數
    - status_forcelist: 需要重試的HTTP狀態碼
    - allowed_methods: 允許重試的HTTP方法
    - timeout: (連接超時, 讀取超時)
    
    返回:
    - requests.Session 物件
    """
    session = requests.Session()
    
    # 設置重試策略
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=allowed_methods
    )
    
    # 設置適配器
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    # 設置預設標頭
    session.headers.update({
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0'
    })
    
    # 設置預設超時
    original_request = session.request
    
    def request_with_timeout(method, url, **kwargs):
        kwargs.setdefault('timeout', timeout)
        return original_request(method=method, url=url, **kwargs)
    
    session.request = request_with_timeout
    
    return session

def test_connection(url, service_name=None, timeout=5):
    """
    測試連接是否可用，增加 DNS 解析和直接 IP 連接
    
    參數:
    - url: 要測試的URL
    - service_name: 服務名稱 ('yahoo_finance', 'mops', 'twse')
    - timeout: 連接超時時間(秒)
    
    返回:
    - bool: 連接是否可用
    - str: 錯誤訊息或成功訊息
    """
    import urllib.parse
    
    # 解析主機名
    parsed_url = urllib.parse.urlparse(url)
    host = parsed_url.netloc
    
    try:
        # 檢查該服務是否被速率限制
        if service_name and service_name in CONNECTION_STATS:
            stats = CONNECTION_STATS[service_name]
            if stats['rate_limited_until'] and time.time() < stats['rate_limited_until']:
                wait_time = int(stats['rate_limited_until'] - time.time())
                return False, f"{host} 處於速率限制中，還需等待 {wait_time} 秒"
    
        # 首先嘗試 DNS 解析
        try:
            ip_address = socket.gethostbyname(host)
            log_connection_event(f"DNS 解析成功: {host} -> {ip_address}")
        except:
            # 如果 DNS 解析失敗，嘗試使用硬編碼的 IP
            ip_address = DOMAIN_IP_MAPPING.get(host)
            if not ip_address:
                return False, f"DNS 解析失敗，且沒有 {host} 的已知 IP 地址"
            log_connection_event(f"使用硬編碼 IP: {host} -> {ip_address}")
        
        # 測試 TCP 連接
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        # 確定端口
        port = 443 if url.startswith('https') else 80
        
        result = sock.connect_ex((ip_address, port))
        sock.close()
        
        if result != 0:
            if service_name and service_name in CONNECTION_STATS:
                CONNECTION_STATS[service_name]['failures'] += 1
            return False, f"無法連接到 {ip_address}:{port}，狀態碼: {result}"
        
        # 如果 TCP 連接成功，嘗試 HTTP 請求
        session = create_robust_session(retries=0, timeout=(timeout, timeout))
        response = session.get(url, allow_redirects=False)
        
        if response.status_code >= 400:
            if response.status_code == 429:
                # 速率限制 - 設置冷卻期
                if service_name and service_name in CONNECTION_STATS:
                    # 設定30分鐘的冷卻期
                    CONNECTION_STATS[service_name]['rate_limited_until'] = time.time() + 1800
                return False, f"收到速率限制回應 (429)，服務暫時無法使用"
            return False, f"HTTP 請求失敗，狀態碼: {response.status_code}"
        
        # 更新連接成功記錄
        if service_name and service_name in CONNECTION_STATS:
            CONNECTION_STATS[service_name]['failures'] = 0
            CONNECTION_STATS[service_name]['last_success'] = time.time()
            if CONNECTION_STATS[service_name]['rate_limited_until']:
                CONNECTION_STATS[service_name]['rate_limited_until'] = None
            
        return True, f"連接成功，狀態碼: {response.status_code}"
        
    except requests.RequestException as e:
        if service_name and service_name in CONNECTION_STATS:
            CONNECTION_STATS[service_name]['failures'] += 1
        return False, f"請求異常: {e}"
    except socket.error as e:
        if service_name and service_name in CONNECTION_STATS:
            CONNECTION_STATS[service_name]['failures'] += 1
        return False, f"Socket 錯誤: {e}"
    except Exception as e:
        if service_name and service_name in CONNECTION_STATS:
            CONNECTION_STATS[service_name]['failures'] += 1
        return False, f"未知錯誤: {e}"

def is_service_available(service_name):
    """
    檢查服務是否可用
    
    參數:
    - service_name: 服務名稱 ('yahoo_finance', 'mops', 'twse')
    
    返回:
    - bool: 服務是否可用
    """
    if service_name not in CONNECTION_STATS:
        return True
    
    stats = CONNECTION_STATS[service_name]
    
    # 如果在速率限制中，服務不可用
    if stats['rate_limited_until'] and time.time() < stats['rate_limited_until']:
        return False
    
    # 如果連續失敗超過5次，服務暫時不可用
    if stats['failures'] >= 5:
        return False
    
    return True

def wait_for_service(service_name):
    """
    等待服務可用
    
    參數:
    - service_name: 服務名稱 ('yahoo_finance', 'mops', 'twse')
    
    返回:
    - bool: 等待是否成功
    """
    if service_name not in CONNECTION_STATS:
        return True
    
    stats = CONNECTION_STATS[service_name]
    
    # 如果在速率限制中，需要等待
    if stats['rate_limited_until'] and time.time() < stats['rate_limited_until']:
        wait_time = int(stats['rate_limited_until'] - time.time())
        log_connection_event(f"{service_name} 處於速率限制中，等待 {wait_time} 秒")
        time.sleep(wait_time)
    
    # 如果連續失敗，需要指數退避等待
    if stats['failures'] > 0:
        wait_time = min(60, 2 ** stats['failures'])
        log_connection_event(f"{service_name} 連續失敗 {stats['failures']} 次，等待 {wait_time} 秒")
        time.sleep(wait_time)
    
    return True

def save_connection_stats():
    """保存連接統計數據"""
    try:
        stats_file = os.path.join(LOG_DIR, 'connection_stats.json')
        
        # 轉換時間戳為 ISO 格式字符串用於 JSON 序列化
        stats_to_save = {}
        for service, stats in CONNECTION_STATS.items():
            stats_to_save[service] = {
                'failures': stats['failures'],
                'last_success': stats['last_success'] and time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats['last_success'])),
                'rate_limited_until': stats['rate_limited_until'] and time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats['rate_limited_until']))
            }
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats_to_save, f, ensure_ascii=False, indent=2)
            
        log_connection_event(f"保存連接統計數據到 {stats_file}")
        
    except Exception as e:
        log_connection_event(f"無法保存連接統計數據: {e}", level='error')

def load_connection_stats():
    """載入連接統計數據"""
    try:
        stats_file = os.path.join(LOG_DIR, 'connection_stats.json')
        
        if not os.path.exists(stats_file):
            return
        
        with open(stats_file, 'r', encoding='utf-8') as f:
            stats_from_file = json.load(f)
        
        # 轉換時間字符串為時間戳
        for service, stats in stats_from_file.items():
            if service in CONNECTION_STATS:
                CONNECTION_STATS[service]['failures'] = stats['failures']
                
                if stats['last_success']:
                    import time
                    try:
                        CONNECTION_STATS[service]['last_success'] = time.mktime(time.strptime(stats['last_success'], '%Y-%m-%d %H:%M:%S'))
                    except:
                        CONNECTION_STATS[service]['last_success'] = None
                        
                if stats['rate_limited_until']:
                    import time
                    try:
                        CONNECTION_STATS[service]['rate_limited_until'] = time.mktime(time.strptime(stats['rate_limited_until'], '%Y-%m-%d %H:%M:%S'))
                        # 檢查是否已過期
                        if CONNECTION_STATS[service]['rate_limited_until'] < time.time():
                            CONNECTION_STATS[service]['rate_limited_until'] = None
                    except:
                        CONNECTION_STATS[service]['rate_limited_until'] = None
        
        log_connection_event(f"已載入連接統計數據")
        
    except Exception as e:
        log_connection_event(f"無法載入連接統計數據: {e}", level='error')

def log_connection_event(message, level='info'):
    """記錄連接事件到日誌"""
    try:
        # 將消息輸出到控制台
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prefix = f"[connection_manager] "
        
        if level == 'error':
            print(f"{prefix}❌ {message}")
        elif level == 'warning':
            print(f"{prefix}⚠️ {message}")
        else:
            print(f"{prefix}ℹ️ {message}")
        
        # 寫入到日誌文件
        log_file = os.path.join(LOG_DIR, 'connection.log')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{now} - {level.upper()} - {message}\n")
    except Exception as e:
        print(f"[connection_manager] 無法記錄日誌: {e}")

# 初始化時載入之前的統計數據
try:
    load_connection_stats()
except Exception as e:
    print(f"[connection_manager] 載入連接統計數據時出錯: {e}")
