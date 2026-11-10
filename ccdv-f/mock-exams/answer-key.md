# CCDV-F 答案速查（簡短版）

詳解見 [questions.md](questions.md)。直接列答案內容，不列選項字母。

| 題號 | 題目主題 | 正確處理方式 |
|---|---|---|
| [Q1](questions.md#q1) | 工具逾時與空結果 | 回傳明確的 Tool Error，保留原始 `tool_use_id`，並以 `is_error: true` 表示執行失敗，讓 Claude 區分「查詢失敗」與「成功但沒有資料」。 |
| [Q2](questions.md#q2) | 重啟後恢復工作階段 | 保存 Session ID，以及對應且已持久化的 Session State；重啟後恢復既有 Session，沿用先前對話、工具互動與相關狀態。只有 ID，卻沒有可恢復的狀態，仍不足以續作。 |
| [Q3](questions.md#q3) | MCP Metadata 中的機密外洩指令 | 將 Server Metadata 視為不可信資料，由 Host／Client 端強制執行安全政策；沒有適當授權就不得傳送 API Keys、Tokens 或其他秘密。工具描述不能覆蓋安全規則。 |
| [Q4](questions.md#q4) | 外部文件要求未授權付款 | 採多層防護：把檢索文字當作資料，限制工具與權限，驗證操作是否符合使用者真正授權的意圖，並對付款等高風險操作設置適當核准。 |
| [Q5](questions.md#q5) | 條件路由與專家委派 | 使用 Routing Workflow：先檢查風險指標，一般案件走原流程，符合條件的案件才委派給專家，再將結構化分析結果交回原 Agent 整合。 |
| [Q6](questions.md#q6) | 結構化提示與來源分隔 | 用清楚標籤分隔指令、保單與評論，明確定義輸出限制，並提供具代表性的輸入／輸出範例，示範模糊或衝突資料應如何依規則處理。 |
| [Q7](questions.md#q7) | 權威證據與過時上下文 | 將權威合約證據與歷史摘要分開，明確標示來源優先順序、版本、日期與是否已被取代，避免舊摘要凌駕目前有效條款。 |
| [Q8](questions.md#q8) | 資料不足時避免幻覺 | 從可靠帳戶來源檢索資料，限制回答只能依已提供的證據；在程式端驗證必要欄位。資料不足時回報資訊不足或停止推論，不能猜測餘額等缺失資訊。 |
| [Q9](questions.md#q9) | 建立外部工單的 MCP Primitive | 提供 MCP Tool，定義清楚的輸入 Schema、行為描述與受控執行流程。建立 Ticket 時仍須驗證參數與使用者權限，必要時要求核准。 |
| [Q10](questions.md#q10) | 不可逆刪除的確認關卡 | 將操作拆成準備／驗證與正式執行兩階段：先確認對象、權限及影響範圍，提供預覽，再取得有效的明確確認，才執行刪除並留下稽核紀錄。 |
| [Q11](questions.md#q11) | Cowork 的工作空間與可審查成果 | 使用限定於指定 Workspace 的 Cowork 任務，審查所需檔案存取範圍，保留來源，將分析輸出存成可供人工檢查的成果。 |
| [Q12](questions.md#q12) | 批次請求的並行與限流控制 | 限制同時執行的請求數，透過感知速率限制的佇列安排請求；失敗時採指數退避與隨機延遲，並設重試上限，遵循服務提供的重試資訊。 |
| [Q13](questions.md#q13) | 獨立工具呼叫的平行執行 | 同時執行兩個工具，完成後把兩個結果放入後續同一則 user 訊息中，各自以正確的 `tool_use_id` 對應原呼叫，再讓 Claude 繼續。 |
| [Q14](questions.md#q14) | 同名工具的結果配對 | 每個 `tool_result` 必須使用產生它的那次工具呼叫之唯一 `tool_use_id`。即使工具名稱相同、完成順序不同，也必須逐一配對原始呼叫。 |
| [Q15](questions.md#q15) | 將模糊需求轉成驗收標準 | 與利害關係人定義可衡量的驗收標準，涵蓋品質、延遲、來源證據、安全與失敗處理，再設計能驗證這些標準的評估。 |
| [Q16](questions.md#q16) | Thinking 設定與快取失效 | Thinking 設定可能改變實際渲染的 Prompt Prefix 或快取適用條件，讓既有快取失效；不能只比較使用者可見文件是否相同。 |
| [Q17](questions.md#q17) | 企業管理設定的優先權 | 企業 Managed Settings 必須保留最高優先權，不能讓較低層的本機或專案設定覆蓋強制安全限制。Repository Owner 身分也不等於有權改企業政策。 |
| [Q18](questions.md#q18) | 長時間遷移任務的檢查點 | 持久化結構化 Checkpoints、核准紀錄、成果與精簡決策摘要；續作時先確認哪些服務完成、哪些變更已核准、哪些實際執行成功，再處理未完成部分。 |
| [Q19](questions.md#q19) | 固定裁定格式的結構化輸出 | 使用 Structured Outputs，提供輸出 JSON Schema 定義欄位、型別與必要值；應用程式仍須處理非正常完成的回應，並驗證資料與業務規則。 |
| [Q20](questions.md#q20) | 使用者選擇的 MCP 調查模板 | 提供 MCP Prompt，明確定義 `service`、`time_range` 等參數，依輸入產生可重用的 Messages／提示模板。模板本身不直接執行調查工具。 |
| [Q21](questions.md#q21) | pause_turn 的正確延續 | 保留暫停的 Assistant Message 與既有歷史，依協定延續同一回合，直到完成或確認失敗；設最大延續次數或逾時限制，避免無限循環。 |
| [Q22](questions.md#q22) | Messages API 的 System 欄位 | 把系統指令放在 Request 最上層的 `system` 欄位；`messages` 保留 user／assistant 對話歷史，不在其中建立 system 角色訊息。 |
| [Q23](questions.md#q23) | 限制各子代理的任務範圍 | 為各專業任務建立有明確範圍的 Subagent，分別限制 Context 與 Tools，定義標準化結果格式，再由 Parent Agent 彙整與驗證。 |
| [Q24](questions.md#q24) | 串流工具參數的組裝 | 依工具 Content Block 累積輸入片段，等區塊完成後組裝完整 JSON，通過解析與 Schema 驗證，再執行工具。 |
| [Q25](questions.md#q25) | HTTP 429 與有界重試 | 遵循 API 的重試指引（如 `retry-after`），採有最大等待上限的指數退避、隨機 Jitter 與有限重試次數；超過限制後依政策回報或交由佇列處理。 |
| [Q26](questions.md#q26) | Thinking Block 的完整性 | 工具往返時原樣保留 API 回傳的 Thinking Blocks、相關 Signatures 與 Assistant Content，再附加工具結果；不要自行改寫或重建思考區塊。 |
| [Q27](questions.md#q27) | MCP Roots 與路徑安全 | 使用 Roots 傳達預期工作範圍，但 Server 仍須獨立驗證每次檔案操作；檢查正規化後的實際路徑、目錄範圍及可能的符號連結繞過。 |
| [Q28](questions.md#q28) | Agent SDK 的工具與路徑權限 | 只提供必要工具，並在每次執行前驗證工具、操作和目標路徑；讀取限於允許範圍，寫入限於指定測試檔案，未授權 Shell 操作應被拒絕。 |
| [Q29](questions.md#q29) | 生產 API 的輸出驗證與安全失敗 | 使用結構化輸出限制，交付下游前驗證 JSON、必要欄位、型別、Enum 與額外欄位。失敗時有限次重試或明確安全失敗，不能 Silent Coercion。 |
| [Q30](questions.md#q30) | Claude Code 分層設定 | 企業限制放 Managed Settings；共用專案設定與規範納入版本控制；開發者偏好使用適當本機／使用者設定，且不得覆蓋企業強制政策。 |
| [Q31](questions.md#q31) | 唯讀內容的 MCP Resources | 將內容作為 MCP Resources，使用穩定 URI 識別；由 Host／Application 選擇與讀取需要的資源，再加入 Context。 |
| [Q32](questions.md#q32) | 穩定前綴與動態資料的快取配置 | 將固定政策手冊與穩定前綴置於 Cache Breakpoint 之前；每次變動的帳戶資料與問題放在之後，讓可重用內容保持一致。 |
| [Q33](questions.md#q33) | Context 超限時的取捨 | 根據問題檢索相關內容，壓縮冗長歷史並去除重複，保留重要決策、證據、來源及版本；為模型輸出預留 Token Budget。 |
| [Q34](questions.md#q34) | 上游 HTTP 503 的工具錯誤 | 回傳 `tool_result`，以 `is_error: true` 標記失敗，保留原始 `tool_use_id`，在內容說明價格服務暫時不可用及 HTTP 503，而非傳空的成功結果。 |
| [Q35](questions.md#q35) | 共用程式庫重構的驗證流程 | 先要求計畫並唯讀分析相依關係及公開介面，審查影響範圍後進行受控修改，執行相關測試，最後檢查 Diff 再決定整合。 |
| [Q36](questions.md#q36) | 固定流程與例外 Agent 的混合架構 | 正常驗證採 Deterministic Workflow；只有例外情況才交給 Bounded Agent，限制其工具、範圍與自主程度，提出必要操作後再進入核准流程。 |
| [Q37](questions.md#q37) | 先釐清需求再實作 | 先完成 Requirements Discovery：定義使用者角色、決策範圍、來源證據、限制、成功指標與失敗處理，再據此設計評估並選擇模型與架構。 |
| [Q38](questions.md#q38) | 動態 Metadata 破壞快取 | 把時間戳記與唯一追蹤碼移到 Cache Breakpoint 後方，保持可重用前綴完全一致；比較整個實際快取前綴，而非只看手冊。 |
| [Q39](questions.md#q39) | 本地 STDIO MCP 的憑證 | 由啟動 Server 的應用程式透過程序環境或本地安全方式提供所需憑證，並保護本地程序執行邊界；不要將 MCP HTTP 認證協定直接搬到 STDIO。 |
| [Q40](questions.md#q40) | 隨程式碼共享的專案規範 | 把簡潔且針對專案的指令寫入 Project-level `CLAUDE.md`，並納入 Git 版本管理，讓規範隨程式碼共享。 |
| [Q41](questions.md#q41) | 檢索網頁中的環境變數外洩指令 | 保留可用證據，但把網頁視為不可信資料，隔離其中指令的影響；限制工具與機密存取，敏感操作須依真正授權及核准規則處理。 |
| [Q42](questions.md#q42) | 統一型別契約與集中驗證 | 定義 Typed Response Contract，如布林資格與受控原因碼；集中驗證模型輸出，再以穩定的應用程式介面交給下游，避免各系統各自解讀自然語言。 |
| [Q43](questions.md#q43) | 付款逾時與重複扣款 | 對同一筆邏輯交易使用相同 Idempotency Key，逾時後先查驗交易狀態，將付款執行與結果確認分開；不可直接把 Timeout 當作未付款並重送新交易。 |
| [Q44](questions.md#q44) | 長期研究的上下文壓縮 | 壓縮或摘要舊對話與工具結果，保留目標、重要決策、證據及其來源、目前進度與待辦，再以精簡狀態延續研究。 |
| [Q45](questions.md#q45) | 選擇合適的 Context 與工具 | 依當前問題挑選相關證據與必要工具，維持指令優先順序，並摘要長期需要保留的狀態；例如退款問題只載入相關政策、交易與工單。 |
| [Q46](questions.md#q46) | 從原型到正式發布的品質關卡 | 建立版本化 Evaluation Suite 與基準比較，達到預定門檻才進入分階段部署；持續監控品質、安全與延遲，並事先定義停止擴大與回滾條件。 |
| [Q47](questions.md#q47) | 用子代理隔離大量搜尋結果 | 將搜尋、篩選與分析委派給專門 Subagent，在其 Context 處理大量中間資料，只回傳主代理需要的相關摘要與證據位置。 |
| [Q48](questions.md#q48) | 代表性測試集與多維評分器 | 建立涵蓋一般、邊界、長文件、缺資料、矛盾與對抗案例的代表性測試集，分別使用 Rubric、Programmatic 與 Safety Graders 評估品質、格式與安全。 |
| [Q49](questions.md#q49) | Agent 的完成條件與執行上限 | 明確定義完成條件、最大回合／工具呼叫數與升級規則；根因、證據、報告與必要驗證完成就停止，無法在限制內完成則回報並適當升級。 |
| [Q50](questions.md#q50) | 政策資料的版本化 RAG | 先檢索符合問題時點與有效版本的相關政策段落，再依證據回答並附引用；不要依賴模型記憶或永遠沿用一次性的靜態摘要。 |
| [Q51](questions.md#q51) | tool_use 不是最終答案 | 執行要求的工具，保留原 Assistant 工具呼叫與對話歷史，把匹配 `tool_use_id` 的 `tool_result` 放在後續 user 訊息，再繼續呼叫直到完成。 |
| [Q52](questions.md#q52) | 個人且限單一專案的設定 | 使用 Project Local Settings 與不進入版本控制的環境變數；`.claude/settings.local.json` 適用於個人、單一專案的設定。 |
| [Q53](questions.md#q53) | CI 中非互動且受限的 Claude Code | 使用 Print Mode、Structured Output 與明確的必要工具 Allowlist，同時滿足非互動、受限權限與可解析結果的要求。 |
