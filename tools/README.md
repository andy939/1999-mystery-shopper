# 出題工具

替 `cstest.json`（智能題庫）補 AI 題，並檢查題目有沒有因為 FAQ 改版而過時。所有指令都在 repo 根目錄執行。每則 FAQ 出 3 題：L1 直述、L2 口語／用詞落差、L3 條件判斷或 L4 錯誤前提／多意圖。

## 流程

1. **挑 FAQ**：`python tools/prep.py [則數] [批數]`
   - 從還沒有 AI 題的 FAQ 裡，依點閱由高到低挑選，每個局處預設最多 40 則（`PER_ORG=80 python tools/prep.py …` 可放寬）
   - 輸出 `tools/work/in_00.json`…（`tools/work/` 不會上傳 GitHub）
2. **出題**：把 `tools/出題說明.md` 複製成 `tools/work/_instructions.md`，並把 id 前綴 `GBB-` 換成新字母（例如 `IBB-`），再請 AI 每批出一個 `tools/work/out_XX.json`
   - 已用過的前綴：G00–G09（2026-09-27）、H00–H25（2026-09-28）、IA／IB／IC／IK（2026-10-09，依等級分批，說明見 batches/2026-10-09/_instructions.md）
   - 子代理同時最多 20 個；中途中斷的批次重跑即可，已完整寫出的檔案可以直接用
3. **合併**：`python tools/merge.py tools/work` 先試跑驗證，沒問題再加 `--write`
   - 會檢查欄位、難度／題型值、FAQ 編號、重複題，並列出應答要點與原文重疊偏低的題數
4. **存檔與發布**：把 `tools/work/` 內容搬到 `tools/batches/日期/`，執行 `python tools/check_stale.py --accept` 把新題的 FAQ 加進快照，commit 並 push

## 檢查題庫有沒有過時

FAQ 每天由爬蟲同步，業管機關改了答覆，題目的應答要點就可能過時（例：2026-10 勞工婚假 8 日改成 14 日）。

**自動執行**：爬蟲每天推送 `data/` 後，GitHub Actions（`.github/workflows/check-stale.yml`）自動檢查，每週一再保險跑一次，也可以在 GitHub 的 Actions 頁手動執行。
- 結果寫進根目錄的 `stale.json`，網站上方會顯示「⚠ 過時 N 題」，🔴 題目暫停出題，🟡 題目標「⚠ 待確認」
- 有過時題目時，GitHub 會開一張「智能題庫有過時題目」Issue（會寄 email 通知）；修好後下次檢查自動關閉

手動執行：`python tools/check_stale.py`，拿 `tools/faq_snapshot.json`（上次確認時的 FAQ 版本）跟最新 FAQ 比對，寫出 `tools/過時檢查報告.md`
  - 🔴 要點數字已過時：數字在舊版 FAQ 有、新版沒有，一定要改
  - 🟡 要點文字在新版找不到：人工確認
  - 另列已下架的 FAQ、答覆有改的 FAQ（附相似度）
- 修好題目後執行 `python tools/check_stale.py --accept`，把快照更新成目前版本，commit 並 push（或在 Claude Code 說「修正過時題目」）

## 紀錄

| 日期 | 批次 | FAQ 則數 | 新增題數 | 題庫合計 |
|---|---|---|---|---|
| 2026-09-27 | G00–G09 | 520 | 1,560 | 2,076 |
| 2026-09-28 | H00–H25 | 1,334 | 4,002 | 6,078 |
| 2026-10-09 | IA／IB／IC／IK | 625＋關鍵詞 200 | 1,025（L0 200、L1 200、L2 205、L3 207、L4 213） | 7,103 |

目前有對話型 AI 題的 FAQ：2,461 則。出題原始檔在 `tools/batches/`。
