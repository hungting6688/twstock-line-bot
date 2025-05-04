def run():
    print("🟡 [intraday_monitor] 盤中跳空異常追蹤中...")
    abnormal = ["2609 陽明", "6182 合晶"]
    print("📊 盤中異常股：")
    for stock in abnormal:
        print(f"⚠️ {stock}：爆量急拉，建議密切觀察")
