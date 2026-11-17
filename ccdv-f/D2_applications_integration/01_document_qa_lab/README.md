# CCDV-F Domain 2 · 文件問答

## 需求規格

使用者可在本機網頁上傳一份 UTF-8 維運報告、對同一份文件連續提問、即時看到答案，並在重新整理後恢復最近的問答。Python 提供 HTTP API，SQLite 保存文件與 session，Claude Messages API 提供串流、結構化回覆與文件前綴快取。本機可用 stub 練習。完成條件包括對三份合成文件執行上傳與問答流程、拒絕無效引用、驗證 session 的延續與重開，以及能在有 API 金鑰時看到兩次請求各自的快取用量。

## 執行

在本 lab 目錄使用 Python 3.10+。預設離線模式，適合用合成報告練習。離線 provider 用英文關鍵字挑選段落，並支援簡單的英文代名詞追問。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -B -m uvicorn app:create_app --factory --host 127.0.0.1 --port 8000
```

開啟 [本機介面](http://127.0.0.1:8000/)，上傳 `samples/checkout-incident.md`，提問 `What triggered the rollback?`。答案會逐段顯示。打開引用可看到文件摘錄。重新整理可載入最近的問答。其他範例包含搜尋索引維護和備份還原報告。

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -v
```

## Session 與 HTTP API

- **重開**。上傳另一份文件或點「用同一份文件開新對話」都會產生新 ID。重開會沿用文件內容，新的 session 從零輪開始。
- **摘要**。預設保留最近四輪完整問答。較早的輪次壓縮為問題、答案摘錄和引用段落編號，最多保留六筆摘要。早於摘要上限的內容會淘汰，讓提示大小有明確邊界。摘要由程式擷取，無須額外呼叫模型。
- **保存**。SQLite 位於 `.local/sessions.sqlite3`。完成且驗證成功才寫入問答。每次寫入檢查資料版本，防止同一 session 的並行請求互相覆蓋。瀏覽器只需記住 session ID 即可在重新整理後載入。

| 方法與路徑 | 行為 |
| --- | --- |
| `POST /api/sessions` | 以 UTF-8 檔案做原始請求本文，並在 `X-Document-Name` 放入 URL 編碼的檔名。 |
| `GET /api/sessions/{id}` | 讀取文件摘要與保留的問答。 |
| `POST /api/sessions/{id}/questions` | 傳入 `{"question":"..."}`。回傳 NDJSON，包含文字 `delta`，以及最後一個 `done` 或 `error`。 |
| `POST /api/sessions/{id}/restart` | 用同一份文件建立空白 session。 |

Claude 回傳 `answer`、`citations` 和 `evidence`。串流時只顯示答案預覽，最後用 Pydantic 驗證 JSON 並檢查引用段落存在、沒有重複，且引用清單符合證據狀態。伺服器從原始文件填入引用摘錄。這些檢查能攔住無效段落編號，引用是否支持每項敘述仍可打開摘錄核對。發生錯誤時，頁面會移除未驗證的預覽。

此 lab 為單人本機執行，資料保存在本機 SQLite。請以合成文件練習。以 Claude 模式提問時，文件與保留的對話上下文會送到 Claude API。

## 真實 Claude 與快取驗收

模型 ID 固定為 `claude-sonnet-4-6`，記錄在 `config.json`。Prompt 存在 `prompts/v1.txt`。調整 prompt 行為時建立新版檔案並更新設定，讓版本可從 Git 查到。模型與 prompt 版本也會顯示在 live 介面。

設定本機環境的 `ANTHROPIC_API_KEY` 後，用 Claude 模式重開伺服器。這會呼叫付費 API。

```powershell
$env:D2_PROVIDER = 'claude'
.\.venv\Scripts\python.exe -B -m uvicorn app:create_app --factory --host 127.0.0.1 --port 8000
```

在另一個終端執行這個驗收腳本。

```powershell
.\.venv\Scripts\python.exe -B check_cache.py
```

腳本先上傳一份帶有測試識別碼的長報告，然後連續提兩個不同的問題。首次使用的文件前綴應有大於零的 `cache_creation_input_tokens`，第二題應有大於零的 `cache_read_input_tokens`。會列印兩次實際 API 用量。文件快取點固定在報告區塊結尾，問題與 session 摘要排在它後面，所以追問變動時文件前綴仍相同。短文件可能低於模型的快取門檻。第二題多帶了對話內容，`input_tokens` 不一定因此下降，應查看快取讀取欄位。離線模式的用量為空。[Claude prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

## 即時與批次

使用者正在等待答案，且下一題可能依賴上一題，所以互動問答使用 Messages API 串流。可延後取回結果的離線評估，例如拿固定文件和題庫做大量回歸測試，才適合放進 Message Batches API。

## 驗證紀錄

- 整合測試涵蓋三份樣本、串流結束、session 恢復與重開、摘要上限、無效引用，以及防止舊的請求寫入覆蓋新答案。
- Chrome 實測通過上傳、串流回答、顯示引用、重新整理恢復、重開對話，以及手機寬度檢查。
- 本次整合檢查發現換文件或重開時，畫面可能保留前一個 session 的問題和錯誤訊息。切換 session 後現在會清空兩者。
- Claude adapter 用模擬的 SDK 回應測試串流文字與用量欄位。有金鑰後以 `check_cache.py` 驗證真正的快取寫入與讀取。
- 本次已做整合自審。課程要求的獨立 code review 仍待完成。
