# ✅ 問題一修正：fundamental_scraper.py 容錯與欄位自動判別
import pandas as pd
import requests
from bs4 import BeautifulSoup

def fetch_fundamental_data():
    print("[fundamental_scraper] 擷取法人買賣超資料...")

    url = "https://www.twse.com.tw/fund/T86?response=html&selectType=ALLBUT0999&date=&_=0"

    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        table = soup.find("table")
        if table is None:
            raise ValueError("無法擷取法人買賣超主表格")

        df = pd.read_html(str(table))[0]

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = df.columns.str.replace(r"\s", "", regex=True)

        print("[fundamental_scraper] 欄位預覽:", df.columns.tolist())

        id_col = [col for col in df.columns if "代號" in col][0]
        buy_col_candidates = [col for col in df.columns if "外資" in col and "超" in col]
        if not buy_col_candidates:
            raise ValueError("❌ 找不到法人買超欄位")
        buy_col = buy_col_candidates[0]

        df = df.rename(columns={id_col: "stock_id", buy_col: "buy_total"})
        df["buy_total"] = df["buy_total"].astype(str).str.replace(",", "").astype(float)
        df["stock_id"] = df["stock_id"].astype(str).str.strip()
        df = df[["stock_id", "buy_total"]].dropna()

        print(f"[fundamental_scraper] ✅ 擷取成功，共 {len(df)} 檔")
        return df

    except Exception as e:
        print(f"[fundamental_scraper] ⚠️ 擷取失敗，自動回傳空資料：{e}")
        return pd.DataFrame(columns=["stock_id", "buy_total"])


# ✅ 問題二修正：run_opening 負責推播，main.py 不要重複推播
# ✅ 問題三＆四：加入技術指標每一項是否命中的 debug log（完整版本）

# 範例片段（放在 ta_analysis.py 的 calculate_technical_scores 中每一項）

# def calculate_technical_scores(df):
#     for _, row in df.iterrows():
#         print(f"[debug] 分析 {row['stock_id']} {row.get('stock_name', '')}")
#         if row.get("macd_hist", 0) > 0 and row.get("macd", 0) > row.get("signal", 0):
#             print("  ✅ 命中 MACD 黃金交叉")
#         if row.get("kdj_k", 0) > row.get("kdj_d", 0) and row.get("kdj_k", 0) < 40:
#             print("  ✅ 命中 KD 黃金交叉")
#         if row.get("rsi_14", 0) > 50 and row.get("rsi_14", 0) > row.get("rsi_14_prev", 0):
#             print("  ✅ 命中 RSI 走強")
#         if row.get("close", 0) > row.get("ma5", 0) and row.get("close", 0) > row.get("ma20", 0) and row.get("close", 0) > row.get("ma60", 0):
#             print("  ✅ 命中均線多頭排列")
#         if row.get("close", 0) > row.get("bb_middle", 0):
#             print("  ✅ 命中布林中線上揚")
#         if row.get("buy_total", 0) > 0:
#             print("  ✅ 命中法人買超")
#         if row.get("eps_growth", False):
#             print("  ✅ 命中 EPS 成長")
#         if row.get("dividend_yield", 0) >= 3 and row.get("ytd_return", 0) > 0:
#             print("  ✅ 命中高殖利率")
