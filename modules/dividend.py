def run():
    print("🟣 [dividend] 高殖利率與 EPS 成長股分析")
    picks = [
        {"name": "2884 玉山金", "yield": "5.2%", "eps": "穩定"},
        {"name": "1402 遠東新", "yield": "6.1%", "eps": "逐年成長"}
    ]
    print("💰 推薦標的：")
    for p in picks:
        print(f"💎 {p['name']}：殖利率 {p['yield']}，EPS {p['eps']}")
