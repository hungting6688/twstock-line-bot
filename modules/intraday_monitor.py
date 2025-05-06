# modules/intraday_monitor.py
print("[intraday_monitor] ✅ 已載入最新版")
from modules.signal_analysis import analyze_stocks_with_signals

def analyze_intraday():
    return analyze_stocks_with_signals(
        limit=150,               # 掃描前 150 大熱門股
        min_score=3,             # 提升推薦門檻
        include_weak=True,       # 顯示極弱股
        filter_type="small_cap"  # 鎖定中小型股
    )
