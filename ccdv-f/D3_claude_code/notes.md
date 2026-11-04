# Domain 3 — Claude Code

> 考試導向重點：先判斷「指引、權限、流程、隔離、持久記憶」是哪一層，再選工具。依本次指定的對話主題整理；版本敏感處另行註明。

## 1. CLAUDE.md vs settings.json

| 項目 | CLAUDE.md | settings.json |
|---|---|---|
| 本質 | 給模型閱讀的 Markdown 指引 | Claude Code 執行環境解析的 JSON 設定 |
| 適合放 | 架構、命名、測試方式、團隊慣例 | permissions、hooks、模型與執行設定 |
| 執行性質 | Probabilistic：靠模型理解並遵守 | 設定的機制由程式套用；permissions／command hooks 可做 deterministic enforcement |
| 例子 | 「提交前請跑測試」 | 用權限拒絕工具，或在執行前用 hook 阻擋 |

- **寫「不要做」不等於技術上禁止。** 必須可靠禁止時，用 permissions／執行前檢查。
- Deterministic 指規則由程式判定，不代表規則一定寫對；依賴 LLM 判斷的 prompt/agent hook 仍具機率性。
- 團隊共用慣例放 **project scope** 並納入版本控制；不要只放某位成員的 user scope。

## 2. Scope 與優先序

設定優先序由高至低：

```text
Managed > CLI > Local > Project > User
```

| Scope | 位置／來源 | 用途 |
|---|---|---|
| Managed | 組織管理設定，例如 managed-settings.json | 組織政策；個人與專案設定不能任意覆寫 |
| CLI | 啟動時的 --settings 等 | 單次 session 設定 |
| Local | .claude/settings.local.json | 個人在此專案的設定，通常不提交 |
| Project | .claude/settings.json | 團隊共用、提交到 Git |
| User | ~/.claude/settings.json | 個人跨專案偏好 |

這是 **settings 的優先序**，不要直接當成 CLAUDE.md 的覆寫演算法。CLAUDE.md 指引會載入並合併到 context。設定陣列可能合併，permission rules 也有自身的 deny／ask／allow 判定，不能假設高層 allow 一定消除低層 deny。參考：[Settings](https://code.claude.com/docs/en/settings)。

## 3. Skills、Subagents、Custom Commands

| 機制 | 解決問題 | 常見形式 | Context |
|---|---|---|---|
| Skill | 重複使用的知識、程序與配套資源 | .claude/skills/<name>/SKILL.md | 通常在目前 context 載入；可設定交由隔離執行 |
| Subagent | 委派專門任務，隔離大量探索內容 | .claude/agents/<name>.md | 自己的 context window |
| Custom command | 用 slash command 快速啟動固定提示／流程 | .claude/commands/<name>.md → /<name> | 通常在目前 session 執行 |

- **Skill = 怎麼做；subagent = 誰負責做；command = 快速啟動什麼。**
- Skills 可依 description 被自動選用，也能用 `/skill-name` 明確呼叫。
- 新版已將 custom commands 整合到 skills 機制；既有 commands 仍可使用。Skill 支援 SKILL.md、參考檔與腳本，功能更完整。
- 不要把「叫用 skill」一律解讀為「產生另一個 agent」。參考：[Skills](https://code.claude.com/docs/en/skills)。

## 4. Subagent：隔離與明確交接

- 一般 subagent **不會自動繼承主對話完整歷史**；系統指引、可用工具、專案設定的載入依類型與設定而異。
- 委派時明確提供：**目標、相關檔案／路徑、必要背景、限制、驗收條件、回傳格式**。
- 錯誤交接：「照剛剛說的修。」正確交接：「檢查 src/auth 的登入失敗，保留公開介面，回傳原因與修改建議。」
- 好處：保護主 context、減少大量日誌污染、專業分工、限制工具權限、可平行處理獨立任務；可依需求選較低成本模型。
- Context 隔離 **不是檔案系統隔離**；同一工作目錄仍可能互相修改檔案，平行寫入須避免衝突。

| 類型 | 常見用途 |
|---|---|
| Built-in Explore | 搜尋與理解程式碼，偏唯讀探索 |
| Built-in Plan | 實作前研究與方案規劃 |
| Built-in general-purpose | 較完整的多步任務 |
| Custom subagent | 自訂 reviewer、debugger 等角色，定義 description、工具、模型與專用指引 |

自訂 subagent 放 `.claude/agents/` 供專案共用，或 `~/.claude/agents/` 供個人跨專案使用。參考：[Subagents](https://code.claude.com/docs/en/sub-agents)。

## 5. Memory：User／Project／Agent

「記住什麼」與「誰能在哪裡使用」要分開判斷。

| 用途分類 | 放什麼 | 何時用 |
|---|---|---|
| User memory／instructions | 個人語言、偏好、跨專案工作習慣 | 希望所有專案都適用；例如 ~/.claude/CLAUDE.md |
| Project memory／instructions | 架構、測試命令、領域規則、團隊慣例 | 此 repository 的長期共同知識；例如 .claude/CLAUDE.md |
| Agent memory | 某個專門 agent 累積的模式、常見問題與經驗 | 希望同一角色跨 session 持續學習 |

- CLAUDE.md 是人維護的指引；**auto memory** 是 Claude 可累積的記憶，並非相同機制。
- 一般 auto memory 通常依專案保存於使用者本機，不等於已提交給團隊的 project CLAUDE.md。
- 單次 session 的 context 不等於持久記憶；要跨 session 保留的重要結論應寫入適合的記憶／文件。

Agent memory 的實際 `memory:` scope 值：

| 值 | 位置 | 選擇時機 |
|---|---|---|
| user | ~/.claude/agent-memory/<agent>/ | 此 agent 的知識要跨專案沿用 |
| project | .claude/agent-memory/<agent>/ | 此專案專用，且希望透過 Git 分享 |
| local | .claude/agent-memory-local/<agent>/ | 此專案專用，但只留在本機 |

**Agent 是用途分類，不是 `memory: agent` 這個合法值。** 參考：[Memory](https://code.claude.com/docs/en/memory)、[Subagent memory](https://code.claude.com/docs/en/sub-agents#enable-persistent-memory)。

## 6. Session 管理

| 指令／概念 | 用途 | 考試判斷 |
|---|---|---|
| claude --continue / -c | 接續目前目錄最近的對話 | 接著剛才的工作 |
| claude --resume <id> / -r <id> | 回到指定 session；未指定時可選取 | 找回特定舊對話 |
| /compact | 將既有對話壓縮為摘要，釋放 context | 同一任務繼續做；細節可能遺失 |
| /clear | 清除目前對話歷史，開始新對話 | 換任務、清掉舊上下文 |
| Fork | 從既有對話分出新的分支，保留原對話 | 比較不同方案／探索替代方向 |

- `/clear` 不會刪除 repository 或持久記憶檔。
- `/compact` 不是清空，也不是保證逐字保留；重要決策應先記錄。
- Session fork 可用 `--fork-session` 搭配 continue/resume；與一般「從乾淨 context 開始的 subagent」不同。
- 對話分支不會自動建立 Git branch 或隔離檔案。參考：[CLI reference](https://code.claude.com/docs/en/cli-reference)。

## 7. Hooks：事件、Matcher、Exit Codes

Hook 在生命週期事件發生時執行；command hook 適合做確定性檢查。它不是寫在 CLAUDE.md 裡的提醒。

| Event | 時機 | 適合用途 |
|---|---|---|
| PreToolUse | 工具執行前 | 檢查參數、禁止危險操作 |
| PostToolUse | 工具成功執行後 | 格式化、驗證結果、記錄；無法撤銷已完成操作 |
| UserPromptSubmit | 使用者提交 prompt、交給模型前 | 驗證 prompt 或補充 context |
| SessionStart | session 啟動／恢復等 | 初始化與載入背景 |
| Stop | 主 agent 準備結束回覆 | 檢查是否完成必要工作 |
| SubagentStop | subagent 準備結束 | 檢查委派結果是否完整 |

### Matcher

Matcher 選擇事件中的哪類對象觸發 hook，例如工具名稱 regex `Bash` 或 `Edit|Write`。它不是用來直接比對 shell 指令內容；檢查實際 command／檔案路徑時，腳本還要解析事件輸入。沒有匹配的工具，該 hook 就不會跑；不是所有事件都支援 matcher。

### Command hook 的基本 exit-code 模式

| Exit code | 基本意義 | 常見考點 |
|---|---|---|
| 0 | Hook 成功；有 JSON 時按事件規格處理 | 純 exit-code 模式通常繼續 |
| 1 | 一般執行錯誤，預設屬 non-blocking | 不是可靠的禁止訊號 |
| 2 | 對支援阻擋的事件發出 blocking 訊號 | PreToolUse 阻擋工具，stderr 提供原因 |

**考試捷徑：用 exit code 預防工具操作 = PreToolUse + exit 2。**

- `PostToolUse + exit 2` 已太晚，只能回饋問題，無法阻止剛才的操作。
- `Stop/SubagentStop + exit 2` 阻止的是「結束」，讓 agent 繼續工作，不是回滾工具操作。
- `SessionStart` 不能靠 exit 2 阻止 session 啟動；exit 2 的效果必須看事件。
- 精確說法：exit 2 不是唯一阻擋方式；PreToolUse 也可 exit 0 並回傳結構化 JSON 的 `permissionDecision: "deny"`。Exit 1 的預設也可能被版本／`onFailure` 設定改變。

參考：[Hooks reference](https://code.claude.com/docs/en/hooks)。

## 8. Headless／CI/CD

| Flag | 用途／限制 |
|---|---|
| -p / --print | 非互動執行，輸出結果後離開；適合腳本／CI |
| --output-format json | 機器可解析的 JSON；搭配 print mode |
| --max-turns N | 限制 agentic turns，控制失控迴圈與執行量；不是 token 上限 |
| --allowedTools | 預先允許所需工具；依最小權限設定 |
| --auto | 教材可能用來泛稱自動執行；不要假定它是所有版本的有效 CLI flag |
| --permission-mode auto | 目前文件中的 auto permission mode；仍有自動風險判斷與適用限制 |
| --dangerously-skip-permissions | 略過 Claude Code 的權限確認；不能當作一般 CI 預設方案 |

```bash
claude -p "Summarize repository conventions" --output-format json --max-turns 5 --allowedTools "Read,Glob,Grep"
```

- **Headless ≠ 所有工具自動獲准。** 無人回覆授權提示時，必要工具須事先以適當政策／allowlist 授權；否則工作可能受阻。
- Auto mode 不等於「所有操作都無條件核准」，也不等於 deterministic permission allowlist。
- `--dangerously-skip-permissions` 只應在已充分隔離、可信且範圍受限的環境審慎使用；它不會賦予 GitHub token／作業系統原本沒有的權限。
- Flags 有版本差異；實作前核對該版本 `claude --help`。參考：[CLI](https://code.claude.com/docs/en/cli-reference)、[Permissions](https://code.claude.com/docs/en/permissions)。

## 9. GitHub Actions：兩層權限

可用 `anthropics/claude-code-action` 將 issue／PR 回應、review 或排程工作接入 GitHub Actions；workflow 通常放在 `.github/workflows/`。

| 層次 | 控制什麼 | 缺少時 |
|---|---|---|
| GitHub 身分／token／workflow permissions | 能否讀 repository、寫 comment、建立／更新 PR | Claude 允許工具也仍會被 GitHub 拒絕 |
| Claude Code tool permissions | agent 能否執行 Bash、Edit、MCP 等工具 | GitHub token 有權也不代表 agent 工具已核准 |

- **兩層都必須允許**；GitHub API 權限與 agent 工具權限不能互相替代。
- API key 放 GitHub **Secrets**，例如 `anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}`；不要提交到 repository。
- API key 用來驗證 Claude／Anthropic，不等於 GitHub repository token。
- 無人值守執行：事先設定觸發條件、明確任務、turn 上限與必要工具授權；依最小權限授權 GitHub 寫入能力。
- 團隊規則仍放 project scope；CI 能讀到提交的設定，不會自動拿到開發者本機的 user/local 設定。

參考：[GitHub Actions](https://code.claude.com/docs/en/github-actions)。

## 10. 專案結構與 Path-specific Rules

```text
repo/
├── .claude/
│   ├── CLAUDE.md              # 專案共用指引；也可用 repo 根目錄 CLAUDE.md
│   ├── settings.json          # 團隊共用設定
│   ├── settings.local.json    # 個人專案設定，通常不提交
│   ├── skills/<name>/SKILL.md # 可重用流程與資源
│   ├── agents/<name>.md       # 自訂 subagent
│   ├── commands/<name>.md     # 既有 slash command
│   └── rules/<topic>.md       # 模組化／依路徑套用指引
└── .github/workflows/         # CI/CD workflows
```

例如 `.claude/rules/typescript.md`：

```markdown
---
paths:
  - "src/**/*.ts"
  - "src/**/*.tsx"
---
Use the project's TypeScript conventions.
Add relevant tests when behavior changes.
```

- `paths` 是 YAML frontmatter 的 glob 清單，讓規則針對匹配路徑載入；省略時為一般規則。
- 路徑規則仍是模型指引，不是檔案存取控制。若要禁止寫入，使用 permissions／PreToolUse guard。
- 考點：**只限某目錄／檔案類型的慣例 → paths frontmatter；強制禁止 → permission／hook。** 參考：[Path-scoped rules](https://code.claude.com/docs/en/memory#path-specific-rules)。

## Exam Shortcuts

| 題目關鍵字 | 優先答案 |
|---|---|
| 團隊共同慣例 | Project CLAUDE.md／project settings，提交 Git |
| 個人跨專案偏好 | User scope |
| 個人在此專案的設定 | Local scope |
| 組織不可被個人覆寫 | Managed settings |
| 「寫規則卻仍違反」 | 指引是 probabilistic；改用 permissions／command hook |
| 執行前禁止操作 | PreToolUse + exit 2（exit-code 題型） |
| 執行後格式化／檢查 | PostToolUse |
| Exit 1 vs 2 | 一般錯誤 vs 事件支援的阻擋訊號 |
| 不希望探索日誌塞滿主對話 | Subagent，明確傳入必要 context |
| 重用程序／專門知識 | Skill |
| 一鍵啟動固定提示 | Custom slash command／skill |
| 專門 reviewer 要記住經驗 | Agent persistent memory；再選 user/project/local |
| 最近 session／指定 session | --continue／--resume <id> |
| 保留工作脈絡、縮小 context | /compact |
| 換新任務、清掉對話 | /clear |
| 從同一歷史探索另一方案 | Fork；不會自動隔離工作檔案 |
| 腳本／CI、結構化結果 | -p + --output-format json |
| 限制 agentic loop | --max-turns |
| 自主執行卻卡授權 | 預先允許必要工具；檢查 GitHub 與 Claude 兩層權限 |
| API key 保存位置 | GitHub Secrets |
| 自動執行 | 不代表略過所有權限；--auto 要核對版本 |
