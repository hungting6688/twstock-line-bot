
---

## 🛠️ 安裝與部署流程

### 1. 建立 GitHub Repository

- 新增一個私人 repo（建議名稱：`twstock-line-bot`）
- 把以上所有檔案依結構建立上去
- 特別注意 `.github/workflows/twstock_scheduler.yml` 要放在正確資料夾

---

### 2. 設定 GitHub Secrets

進入 Repo → Settings → Secrets and variables → Actions → New repository secret  
新增以下四個 Secrets：

| Secret 名稱                | 說明                   |
|-----------------------------|------------------------|
| `LINE_CHANNEL_ACCESS_TOKEN` | 你的 LINE Bot 權杖 |
| `LINE_USER_ID`              | 你的個人 LINE User ID（接收推播的人） |
| `GOOGLE_SHEET_ID`           | 你的 Google Sheets 文件 ID |
| `GOOGLE_SHEET_KEY_JSON`     | base64 編碼後的 Google 金鑰 JSON |

---

### 3. 啟用 GitHub Actions 排程

- `.github/workflows/twstock_scheduler.yml` 會自動設定每天五時段執行
- 不用自己開啟，只要檔案放正確、Secrets 填好，GitHub 會自動排程！

---

### 4. 測試

可以在 GitHub → Actions 頁面手動點「Run workflow」測試一次  
確認 LINE 有收到訊息，排程就是正常的！

---

## ✨ 額外功能說明

- 每日五時段：08:30 / 09:00 / 12:00 / 13:00 / 13:40
- 每週六早上推播週報
- 自動從 Google Sheets 抓取你的自訂追蹤股清單
- 後續可擴充技術指標分析、股息預估、圖表生成等功能！

---

# 🛡️ 注意事項

- GitHub Actions 免費版每月有 2,000 分鐘配額（你的推播大約用掉 200 分鐘，非常安全）
- Google Sheets 金鑰請務必 base64 編碼後填入，保護安全！

---
