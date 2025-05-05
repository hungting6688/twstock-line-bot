from modules.signal_analysis import analyze_stocks_with_signals

def analyze_dividend():
    return analyze_stocks_with_signals(
        title="💰 殖利率與短期潛力推薦",
        limit=100,
        min_score=2.2,
        filter_type="small_cap",
        include_weak=True
    )
