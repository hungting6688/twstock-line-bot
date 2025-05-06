return analyze_stocks_with_signals(
    mode="opening",  # <== 要設定正確
    limit=100,
    min_score=3.5,
    filter_type=None,
    include_weak=True
)
