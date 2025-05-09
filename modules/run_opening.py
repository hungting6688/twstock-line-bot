for idx, row in df_result.iterrows():
    try:
        print(f"[debug] row[{idx}] = {row.to_dict()}")  # ✅ 印出整列原始資料

        label = str(row.get("label") or "📌")
        stock_id = str(row.get("stock_id") or "")
        stock_name = str(row.get("stock_name") or "")
        score = str(row.get("score") or "-")
        reasons = str(row.get("reasons") or "-")
        suggestion = str(row.get("suggestion") or "-")

        lines.append(
            f"{label}｜{stock_id} {stock_name}｜分數：{score} 分\n"
            f"➡️ 原因：{reasons}\n"
            f"💡 建議：{suggestion}\n"
        )
    except Exception as row_err:
        print(f"[run_opening] ⚠️ 單列錯誤：{repr(row_err)} at row {idx}")
