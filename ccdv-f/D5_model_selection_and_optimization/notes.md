# Domain 5 — Model Selection & Optimization

## 1. Token Fundamentals

### Token

Token 是模型處理文字的基本單位。

粗略估計：

- 約 3–4 characters ≈ 1 token
- 約 0.75 English words ≈ 1 token

實際 token 數會依 tokenizer 與語言而不同。

### Input Tokens

包含送進 request 的所有內容：

- System prompt
- Messages / conversation history
- Tool definitions
- Images / documents

### Output Tokens

包含：

- Claude response
- Thinking tokens

### Context Window

Context window = 單次 API call 可使用的總容量。

```text
system prompt
+ messages
+ tools
+ images/documents
+ output
+ thinking
<= context window
```

所有內容都會競爭同一個 context window。

### `max_tokens`

`max_tokens` **只限制 output token 上限**。

它不會：

- 擴大 context window
- 讓 Claude 看更多 conversation history
- 降低 token 單價
- 自動提高回答品質

> `max_tokens` = output cap, NOT memory expansion.

如果 context 快滿：

```text
不要 increase max_tokens
→ prune / compact / summarize context
```

---

## 2. Token Cost

Output tokens 通常比 input tokens 貴很多。

本課程常以：

```text
Output ≈ 3–5× Input cost
```

作為判斷。

因此即使 output tokens 數量較少，也可能主導整體帳單。

### Cost Formula

```text
Daily Cost =
requests_per_day
×
(
  avg_input_tokens × input_price
  +
  avg_output_tokens × output_price
)
```

### Cost Optimization

不要只看 input。

應避免：

- 過度 verbose output
- 不必要欄位
- 重複說明
- 過長 thinking

> Output efficiency matters because output tokens are expensive.

---

## 3. Token Counting API

可以在真正 inference 前使用：

```python
client.messages.count_tokens(...)
```

用途：

- Estimate input token usage
- Context planning
- Cost estimation
- Detect oversized requests

### Tokenizer

Tokenizer = 把文字拆成 tokens 的元件／規則。

不同 model generation 可能使用不同 tokenizer。

因此：

> 換模型時應重新 count tokens。

相同文字在新版 tokenizer 下可能產生更多 tokens。

---

# 4. Model Tiers

## Haiku

適合：

- Classification
- Routing
- Simple extraction
- High-volume workloads

特色：

- Fast
- Cheap
- 適合大量簡單任務

## Sonnet

適合：

- General-purpose
- Coding
- Writing
- Analysis
- Multi-step tasks

通常是預設的 balanced choice。

## Opus

適合：

- Deep reasoning
- Complex agentic coding
- Difficult analysis
- Accuracy-critical tasks

成本與 latency 較高。

## Fable

教材定位：

- Long-running agents
- Frontier agentic work
- Advanced research

---

# 5. Right-Sizing Strategy

核心：

> Use the smallest model that meets the required quality.

不是越大的 model 越好。

## Start Cheap

適合：

- Prototyping
- High-volume workloads
- Cost-sensitive tasks
- Latency-sensitive tasks
- Simple tasks

流程：

```text
Haiku
→ evaluate
→ upgrade only if a capability gap is proven
```

## Start Capable

適合：

- Complex reasoning
- Accuracy outweighs cost
- Difficult production tasks

流程：

```text
Opus
→ establish quality
→ optimize
→ try down-tier later
```

### Exam Pattern

```text
High-volume classification
→ try Haiku first
```

---

# 6. Effort Before Switching

`effort` 用來調整：

- reasoning depth
- latency
- cost

而不必直接換 model tier。

如果：

```text
Opus quality is required
BUT Opus is too slow / expensive
```

不要第一步直接換 Sonnet。

先：

```text
Lower effort
→ evaluate quality
→ switch model only if needed
```

> Tune effort before changing tiers.

### Effort Levels

| Level  | Use                              |
| ------ | -------------------------------- |
| low    | lookup, routing                  |
| medium | standard tasks                   |
| high   | general-purpose                  |
| xhigh  | deeper reasoning, coding, agents |
| max    | research, complex analysis       |

More effort ≠ always better.

---

# 7. Tiered Routing

大量 request 不一定全部使用昂貴模型。

典型流程：

```text
Incoming request
→ Haiku triage
→ evaluate difficulty/confidence
   ├─ easy / high confidence → Haiku
   └─ difficult / low confidence → Sonnet / Opus
```

目標：

> Cheap average cost + strong quality on difficult cases.

### Confidence

Confidence 通常是 application-defined/model-generated signal。

例如：

```json
{
  "category": "technical",
  "confidence": 0.88
}
```

注意：

> `0.88` 不是 Claude API 提供的真實 probability。

模型自己輸出的 confidence 必須透過 eval 校準，不能直接當成真正 88% accuracy。

---

# 8. Cost Reduction Priority

本課程成本優化順序：

```text
1. Right-size model
2. Prompt caching
3. Batch API
4. Reduce output
5. Context management
```

完整 optimization stack 還可加入 effort：

```text
Model
→ Effort
→ Cache
→ Batch
→ Prune context
→ Reduce output
```

核心：

> Cheapest, fastest CORRECT answer wins.

不能為了省成本犧牲 required correctness。

---

# 9. Prompt Caching

Prompt caching 用來降低**重複 input** 的成本。

適合：

- Long system prompts
- Repeated tool definitions
- Repeated documents
- Fixed few-shot examples

## Important Terms

### Static Prefix

每次 request 都相同的前綴內容。

### Cache Hit

找到相同的 cached prefix，可直接重用。

### Cache Miss

沒有匹配 cache，需要重新處理。

### TTL — Time To Live

Cache 的有效期限。

教材：

- default TTL ≈ 5 minutes
- 也有較長 TTL 選項

### Cache Invalidation

Cached prefix 被改變，導致舊 cache 失效。

---

## Cache Placement

原則：

> Stable first, dynamic later.

推薦順序：

```text
Tool definitions
→ Static system prompt
→ Few-shot examples
→ Dynamic user message
```

動態內容例如：

- Timestamp
- UUID
- User-specific values

應放 cached portion 後面。

### Exam Trap

```text
Timestamp in cached prefix
→ every request differs
→ cache miss
```

---

## Minimum Size

本課程考點：

```text
Static cached prefix >= ~1,024 tokens
```

太短的 prompt 不適合 caching。

---

## Cache Economics

教材範例：

```text
First cache write
→ slightly more expensive

Later cache hit
→ ~90% reduction in repeated input cost
```

因此 cache 適合：

> 大段、固定、會重複很多次的 input。

不適合：

> short + one-time request。

---

# 10. Batch API

Batch API = asynchronous bulk processing。

流程概念：

```text
Prepare many requests
→ create batch
→ process asynchronously
→ retrieve results later
```

## 適合

- Overnight jobs
- Bulk extraction
- Large eval suites
- Large classification jobs
- Non-urgent processing

## 不適合

- User-facing chat
- Interactive workflows
- Blocking pre-merge CI
- User currently waiting

### Exam Rule

```text
Lots of work + can wait
→ Batch API

User / CI pipeline waiting
→ NOT Batch
```

## `custom_id`

每一筆 Batch request 可使用 `custom_id`。

用途：

> 將 Batch output 對回原始 request。

例如：

```text
req-001 → invoice A
req-002 → invoice B
```

結果回來後依 `custom_id` 對應。

### Course Specs

本教材提到：

- Up to 100,000 requests/batch
- 256 MB
- Processing window up to 24h
- Results retained for a limited period

考試核心仍是：

> Batch = bulk + async + non-urgent.

---

# 11. Cache + Batch

Caching 和 Batch 不是二選一。

可以：

```text
Prompt caching
+
Batch API
```

一起使用。

例如：

```text
8,000 invoices
+ same 3,000-token system prompt
+ overnight processing
```

→ Cache + Batch

判斷：

```text
Repeated static prefix
→ Cache

Bulk + async
→ Batch

Both true
→ Cache + Batch
```

---

# 12. Context Management

舊資料留在 context 不只占容量，也會增加成本。

如果某個 10 turns 前的 tool result 還在 conversation history：

> 它後續每一輪都可能繼續算 input tokens。

## Context Cleanup

### Clear Old Tool Results

移除已經不需要的 tool outputs。

### Compaction

把長 conversation 濃縮成 summary。

### Selective Tool Results

只傳後續需要的欄位。

例如原 tool response：

```json
{
  "status": "shipped",
  "debug_data": "...",
  "raw_payload": "...",
  "internal_metadata": "..."
}
```

後續只需要：

```json
{
  "status": "shipped"
}
```

就不要一直保存整包 JSON。

---

## 85% Context Scenario

如果：

```text
Context = 85% full
原因 = old tool results
```

錯誤做法：

```text
increase max_tokens
switch to bigger model immediately
```

正確：

```text
prune
compact
summarize
remove old tool payloads
```

好處：

- Free context capacity
- Reduce per-turn input cost

> Context full because of old data → clean it, don't enlarge it.

---

# 13. Adaptive vs Extended Thinking

## Adaptive Thinking

模型自己決定思考多少。

Developer 使用：

```text
effort
```

來調整 reasoning depth。

概念：

```text
model decides thinking amount
```

## Extended Thinking

Developer 手動指定：

```text
budget_tokens
```

本課程最低：

```text
1,024 tokens
```

概念：

```text
developer sets thinking budget
```

### Exam Shortcut

```text
Adaptive → model decides
Extended → developer sets budget_tokens
```

---

## Thinking Cost

Thinking tokens：

- consume context window
- billed at output rates
- increase latency

因此：

> More thinking is NOT universally better.

簡單 lookup 不需要大量 thinking。

複雜 reasoning 才值得增加。

非常大的 thinking workload，如果不需要即時結果，可考慮 Batch API。

---

# 14. Deployment Platforms

Claude 可透過不同平台使用：

| Platform          | Authentication          |
| ----------------- | ----------------------- |
| Claude API direct | API key                 |
| Amazon Bedrock    | AWS credentials / SigV4 |
| Google Vertex AI  | GCP credentials         |
| Microsoft Foundry | Azure credentials       |

## SigV4

SigV4 = AWS Signature Version 4。

是 AWS request authentication/signing 機制。

不需要在本章背演算法細節。

### Key Principle

Messages API 的概念大致一致：

```text
model
messages
tools
max_tokens
...
```

主要差異：

- Authentication
- IAM / cloud integration
- Feature availability
- Compliance requirements

> Choose provider based on cloud/compliance/auth requirements, not because Claude becomes a different model.

---

# 15. Strategy Selector

## Real-time chatbot + repeated long system prompt

```text
Prompt caching
```

不是 Batch，因為使用者正在等待。

## Overnight bulk processing + repeated system prompt

```text
Caching + Batch
```

## One-off short prompt

```text
Neither
```

## Blocking Pre-Merge CI + repeated system prompt

```text
Prompt caching
```

不是 Batch，因為結果必須即時完成。

---

# Exam Shortcuts

```text
max_tokens
→ output cap only

Context almost full
→ prune / compact / summarize

Same long prefix repeated
→ Prompt caching

Dynamic timestamp before cached prefix
→ cache miss / invalidation

Bulk + non-urgent
→ Batch API

Interactive chat
→ NOT Batch

Blocking CI
→ NOT Batch

Classification / routing / high volume
→ Haiku

General-purpose
→ Sonnet

Deep reasoning
→ Opus

Need current model quality but too slow/expensive
→ lower effort first

Easy requests + occasional hard cases
→ Tiered routing

Output tokens
→ more expensive than input

Old tool results
→ continue consuming context/input cost

Adaptive thinking
→ model decides

Extended thinking
→ developer sets budget_tokens

Cost optimization
→ Model → Cache → Batch → Output → Context
```

## Final Mental Model

```text
Choose the smallest model that meets quality
↓
Tune effort
↓
Cache repeated input
↓
Batch non-urgent bulk work
↓
Remove unnecessary context
↓
Keep output concise
```

> The cheapest, fastest correct answer wins.
