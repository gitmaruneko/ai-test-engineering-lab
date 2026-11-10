# Domain 6 — Prompt & Context Engineering

> 考前速讀：依本次指定主題與原對話可讀取內容整理；模型相容性不延伸到特定版本。

## 1. Prompt：把需求說清楚

- **Vague → Explicit**：`Extract the key information` 太模糊；明訂任務、欄位名稱、輸出格式、限制與缺資料時的處理方式。
- **Role assignment ≠ reasoning depth**：角色設定引導專業視角、語氣與關注點；「你是專家」本身不保證推理更深入或答案正確。
- **System prompt**：放穩定角色、核心規則與輸出要求；每次呼叫都要提供必要指令。
- **Stateless API**：不要假設模型記得上次請求；應用程式負責帶入必要歷史、摘要與狀態。
- **XML tags**：用 `<instructions>`、`<document>`、`<examples>` 分隔指令、資料與範例，減少混淆；標籤本身不是安全或正確性保證。
- **Few-shot**：給代表性的輸入／輸出範例，示範格式、分類邊界與例外；範例須一致，避免把錯誤模式教給模型。

## 2. 推理與輸出控制

- **Chain of Thought（CoT）**：分步處理適合需要推理的任務；推理過程較長不等於答案必然正確。
- **Native thinking**：模型原生的思考能力／機制，與在 prompt 加一句「step by step」不同；不應假設完整內部推理一定會成為可見文字。
- **Prefill**：預填 assistant 開頭（例如 `{`）來引導續寫；**部分新模型不支援，可能回 400**，不能當通用方案。
- **Structured Outputs / `tool_use`**：需要穩定機器可讀格式時，優先採用 schema 約束的輸出方式；不要只依賴「請回 JSON」或 prefill。實際保證程度取決於所用功能。
- **Syntax ≠ semantics**：合法 JSON／符合 schema，不代表內容真實、分類正確或業務規則成立。
- **Validation**：解析後仍檢查欄位型別、必要值、範圍、跨欄位關係與來源依據；驗證失敗須有明確處理流程。

## 3. Schema：不要逼模型猜

| 反模式 | 修正與考點 |
| --- | --- |
| 來源可能沒有 `po_number`，卻要求一定填字串 | 允許 `null`，明訂缺值規則；避免捏造或亂填 `"N/A"`。欄位可以 required，但值允許 null。 |
| enum 只有 `bug / feature / question`，實際出現 complaint | 提供 `other`／`unclear` escape hatch，避免硬塞進錯誤類別。 |
| 把 schema 合法當成內容正確 | 格式檢查之外，仍需語意與業務驗證。 |

- **`other`**：資料可理解，但不屬於現有類別；**`unclear`**：資訊不足，無法可靠判定。

## 4. Context：當成有限預算管理

- **Context as a budget**：指令、歷史、文件、工具結果都占用空間；保留與任務相關的高價值資訊，並預留回答空間。
- **Progressive summarisation**：逐步摘要較舊內容，保留目標、限制、決策、關鍵事實與待辦；摘要可能遺失細節，不等於原文。
- **Compaction**：壓縮／移除冗餘歷史，留下可繼續工作的狀態，避免整段對話無限累積。
- **Scratchpad / memory tools**：把中間狀態或可持續使用的資訊外部化，需要時再讀回；不能假設 API 自動永久記憶。
- **Quote-then-answer**：先擷取相關原文，再依證據回答，提升長文件答案的可追溯性；仍須核對引文與結論。
- **Lost-in-the-middle**：長 context 中間的資訊較易被忽略。關鍵規則放 system／開頭，或在使用者訊息結尾重申；單純增加 `max_tokens` 無法解決位置問題。

## 5. API：先看停止原因，再處理內容

| `stop_reason` | 應用程式應做什麼 |
| --- | --- |
| `tool_use` | 模型正在要求工具；執行工具 → 回傳對應 `tool_result` → 讓模型繼續，不能直接當最終答案。 |
| `max_tokens` | 可能被截斷；不要直接當完整答案或完整 JSON，應檢查並依流程續接／重試。 |
| `end_turn` | 本輪自然結束；再依內容與驗證結果決定如何呈現。 |
| 其他原因 | 明確分支處理，不能全部視為成功完成。 |

- **Defensive parsing**：`content` 是多個具型別的 blocks；依 `type` 處理文字、工具呼叫等，不假設 `content[0].text` 一定存在。
- 同一回應可能含多個 blocks／工具呼叫；保留工具呼叫 ID 與結果對應，不把工具要求誤當一般文字。

## 6. 長對話穩定性與 Drift Defence

- **Long-session degradation / context pollution**：歷史過長、過時指令、無關工具結果與矛盾範例，會干擾當前任務，造成格式或行為漂移。
- **Mid-conversation reinforcement**：後續請求重新注入核心規則與格式要求；依 API 支援方式更新 system／高優先級指令，不假設任意插入一則 system 訊息都有效。
- **Drift defence**：重申關鍵規則 + Structured Outputs／`tool_use` + 壓縮舊歷史 + 驗證結果。
- **Session limits**：設定對話長度／context 門檻；達門檻時摘要交接、重建乾淨 session，並重新帶入必要規則與狀態。
- **Consistency stack**：
  1. **Structured Outputs／`tool_use`**：提高格式與結構穩定性。
  2. **Model version pinning**：固定版本，降低模型更新造成的行為變動。
  3. **Eval suite in CI**：prompt／模型變更時跑評測，檢查分類、語意、格式與例外情境的 regression。

## 7. 考試速記與常見陷阱

| 題目線索 | 優先反射 |
| --- | --- |
| Prompt 模糊、輸出不一致 | 明訂格式、欄位、限制；不是只加「你是專家」。 |
| 需要深入推理 | 區分角色設定與推理機制；不要只看角色頭銜。 |
| JSON 合法但答案錯 | 語意／業務驗證；schema 不保證事實正確。 |
| 欄位在來源不存在，模型卻填值 | 允許 null；檢查 required + 非 nullable 的設計。 |
| enum 強迫選錯類別 | 加 `other`／`unclear`。 |
| 100k context 的中間規則被忽略 | Lost-in-the-middle → 關鍵指令移到開頭／結尾。 |
| `stop_reason = tool_use` | 執行工具並回傳結果，繼續迴圈。 |
| 第 10 輪正常，第 30 輪 JSON 變 Markdown | Prompt drift → 中途強化規則、結構化輸出、整理 context。 |
| 新模型使用 prefill 回 400 | 檢查相容性；優先考慮支援的結構化輸出方案。 |
| 模型／prompt 更新後結果變動 | 固定模型版本 + CI eval，不能只靠單次成功範例。 |

> **Prefill steers. Schema enforces. Eval verifies.**  
> **結構符合 ≠ 語意正確；context 很長 ≠ 每段都會被同等注意。**
