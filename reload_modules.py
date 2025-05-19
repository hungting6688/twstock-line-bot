"""
使用強制重新加載模組的腳本
將此文件保存為 reload_modules.py
"""

import sys
import importlib
import os

# 強制重新加載模組
modules_to_reload = [
    'modules.analysis.sentiment',
    'modules.multi_analysis',
    'modules.data.finance_yahoo',
    'modules.data.scraper'
]

def reload_module(module_name):
    """強制重新加載指定模組"""
    try:
        if module_name in sys.modules:
            print(f"[reload] 移除現有模組: {module_name}")
            del sys.modules[module_name]
        
        print(f"[reload] 重新導入模組: {module_name}")
        importlib.import_module(module_name)
        print(f"[reload] ✅ 已成功重新加載: {module_name}")
        return True
    except Exception as e:
        print(f"[reload] ❌ 重新加載失敗: {module_name}, 錯誤: {e}")
        return False

if __name__ == "__main__":
    print("[reload] 開始強制重新加載模組...")
    
    # 檢查 modules.analysis.sentiment 是否包含 pandas 導入
    try:
        module_path = os.path.join("modules", "analysis", "sentiment.py")
        if os.path.exists(module_path):
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "import pandas as pd" not in content:
                    print(f"[reload] ⚠️ 文件 {module_path} 中未找到 pandas 導入")
                    print("[reload] 自動添加 pandas 導入...")
                    
                    # 修改文件添加 pandas 導入
                    with open(module_path, 'w', encoding='utf-8') as fw:
                        if "import yfinance as yf" in content:
                            modified_content = content.replace(
                                "import yfinance as yf", 
                                "import yfinance as yf\nimport pandas as pd"
                            )
                            fw.write(modified_content)
                            print("[reload] ✅ 已添加 pandas 導入")
                        else:
                            # 如果找不到常見的導入位置，添加到文件開頭
                            new_content = 'import pandas as pd\n' + content
                            fw.write(new_content)
                            print("[reload] ✅ 已添加 pandas 導入到文件開頭")
    except Exception as e:
        print(f"[reload] ⚠️ 檢查/修改 sentiment.py 時出錯: {e}")
    
    # 重新加載所有模組
    for module in modules_to_reload:
        reload_module(module)
    
    print("[reload] 模組重新加載完成")
