# Messages API

## The Stateless Messages API

### Core Rule

> The Messages API is stateless.

Claude does not remember previous API calls automatically.

The application must send the conversation history on every turn.

### Multi-Turn Conversation

```text
User message
→ Send messages[]
→ Claude response
→ Append assistant response
→ Append next user message
→ Send full messages[] again
```

## Vision, Prefill & Thinking

### Vision

- Send image blocks together with text.
- Used for document/image analysis and multimodal workflows.

### Prefill

- Seeds the assistant response to steer output format.
- Not supported on newer models such as Opus 4.6+ / Sonnet 4.6.

### Adaptive Thinking

- The model decides whether and how much to think per request.
- Can be guided with `effort`.
- Do not assume every turn includes a thinking block.

### Extended Thinking

- Uses a fixed `budget_tokens`.
- Minimum budget: 1024.
- Very large budgets (>32K) may be better suited to Batch API.

### Exam Notes

- More thinking is not always better.
- Simple tasks may not benefit from thinking.
- Thinking is incompatible with forced `tool_choice` (`any` / specific tool).
- Use `tool_choice="auto"` when thinking is enabled.

**Adaptive = let the model decide**
**Extended = I need explicit budget control**


## Streaming, Batch & Prompt Caching

### 1. SSE Streaming

#### Core Idea

Streaming lets the response arrive incrementally as it is generated.

> Streaming = reduce perceived latency for user-facing applications.

#### Event Flow

`message_start`
→ many `content_block_delta`
→ `message_stop`

#### When to Use

- Chatbot
- Interactive application
- User is waiting for the answer
- Need to show output as soon as possible

#### Exam Cue

- User-facing latency → Streaming
- `overloaded_error` in stream → HTTP 529

---

### 2. Batch API

#### Core Idea

Batch API is for large-volume, asynchronous, non-real-time processing.

> Batch = bulk + async + lower cost

#### Course Facts

- About 50% lower cost than standard API
- Up to 100,000 requests or 256 MB per batch
- Processing window up to 24 hours
- Results available for 29 days
- Single-turn only
- Not suitable for multi-turn agent loops

#### Good Use Cases

- Overnight processing
- Large-scale classification
- Bulk summarization
- Offline log analysis
- Weekly reports

#### Not Suitable For

- Chatbot
- Interactive user-facing request
- Blocking CI check
- Multi-turn agent

---

### 3. Prompt Caching

#### Core Idea

Use prompt caching when many requests reuse the same large context.

> Prompt Caching = reduce cost of repeated input context

#### Common Cache Candidates

- Tool definitions
- System prompt
- Shared examples
- Long reference documents
- Policies / guidelines

#### Course Facts

- Cache read ≈ 10% of normal input price
- Up to ~90% saving on repeated prefix
- Minimum cacheable prefix: 1,024 tokens
- Default TTL: 5 minutes
- 1-hour TTL available
- Break-even roughly around 2 requests with the same prefix

---

### 4. Stable Prefix

Stable prefix means:

> The repeated, unchanged beginning of an API request.

Example:

Stable:

- tools
- system prompt
- shared reference document

Dynamic:

- current user question
- timestamp
- UUID
- user ID
- request-specific data

#### Key Rule

> Stable first, dynamic later.

---

### 5. Cache Breakpoint

A cache breakpoint is NOT text like `---`.

It is defined in the API request using `cache_control`.

Conceptually:

`stable tools`
→ `stable system prompt`
→ `stable document`
→ **cache breakpoint**
→ `dynamic user input`

#### Important

The application decides where the cacheable prefix ends.

You do NOT write:

`--- cache starts here`

inside the user's normal prompt.

---

### 6. Common Caching Mistake

#### Problem

Dynamic data appears before the cache breakpoint.

Example:

`timestamp`
→ `UUID`
→ `system prompt`
→ breakpoint

Because timestamp / UUID changes every request, the prefix changes every time.

Result:

> Cache hit rate ≈ 0%

#### Fix

Move dynamic content AFTER the breakpoint.

`tools`
→ `system`
→ `document`
→ breakpoint
→ `timestamp`
→ `UUID`
→ `user question`

---

### 7. Stream vs Batch vs Cache

#### Decision Rule

- User-facing / interactive → Streaming
- Large bulk offline work → Batch API
- Large repeated context → Prompt Caching
- Blocking workflow → synchronous API

#### Important

Batch + Prompt Caching can be combined.

Example:

50,000 support tickets overnight
→ Batch API

If every ticket also uses the same system prompt + examples
→ Batch API + Prompt Caching

---

### 8. CI Pre-Merge / Blocking Workflow

#### CI Pre-Merge

Before code is merged, CI runs checks such as:

- unit tests
- build
- lint
- security checks
- firmware validation
- AI review

Flow:

PR
→ run check
→ PASS → merge
→ FAIL → block merge

#### Blocking Workflow

A blocking workflow means:

> The next step cannot continue until the current result is available.

Therefore:

Pre-merge CI
→ needs result now
→ synchronous API

NOT Batch API.

---

### 9. Large Repeated Document Case

Example:

Every request includes the same 100K-token book.

Without cache:

- Claude repeatedly processes the same large context
- higher input cost
- slower first token

With prompt caching:

First request:
→ cache write

Later requests:
→ cache read

Benefits:

- lower input cost
- faster time-to-first-token

---

### My Questions / Clarifications

#### Q1. What is stable prefix?

It is the part of the API request that stays the same across requests.

Not the user's changing question.

Example:

Stable:

- system prompt
- tools
- reference docs

Dynamic:

- user prompt
- timestamp
- request data

---

#### Q2. Does it mean the first half of the prompt is fixed and the second half changes?

Conceptually yes, but more accurately:

It is not simply "first half vs second half."

The important point is:

> Everything before the cache breakpoint should remain stable.

---

#### Q3. What is a cache breakpoint? Is it written in the prompt using `---`?

No.

It is API metadata, usually through `cache_control`.

`---` is only a visual explanation.

---

#### Q4. Is prompt caching only for agents?

No.

Prompt caching is an API/application-level feature.

It can be used by:

- normal API calls
- agents
- document Q&A systems
- multi-turn applications

The application does not have to be an agent.

---

#### Q5. If every user prompt is different, how can anything be fixed?

You are NOT caching the user's changing prompt.

You cache the repeated background context.

Example:

Fixed:

- system prompt
- tools
- company manual

Changing:

- user question

So:

> Cache repeated context, not repeated user questions.

---

#### Q6. Do I receive the prompt first and then filter/sort it?

Usually no.

The application should be designed in advance to separate:

- stable context
- dynamic request content

Flow:

Application defines stable prefix
→ receives user input
→ places user input in dynamic section
→ sends API request

---

#### Q7. What is CI pre-merge?

It is an automated check before code is allowed to merge.

Example:

PR
→ CI test
→ PASS → merge
→ FAIL → block

Because the merge is waiting for the result, it is a blocking workflow.

---

#### Q8. What is a blocking workflow?

A workflow where the next step cannot proceed until the current step finishes.

Example:

AI validation
→ wait for result
→ PASS → merge

Therefore it normally needs a synchronous API call.

---

#### Q9. What is Batch API?

Batch API lets you submit many independent requests for asynchronous processing.

Best for:

- lots of data
- non-real-time jobs
- overnight processing
- lower cost

Not for:

- immediate answers
- chatbot
- blocking CI
- multi-turn agent loops

---

### Exam Shortcut

> Interactive → Streaming
> Bulk offline → Batch
> Repeated context → Cache
> Blocking workflow → Synchronous

And for caching:

> Stable first, dynamic later.

## The Ignored Convention

### New teammate misses team conventions

Cause:
- Conventions stored in User scope

Fix:
- Move to Project scope
- Use `.claude/CLAUDE.md`
- Commit to git

### CLAUDE.md says "NEVER" but Claude still does it

Cause:
- CLAUDE.md is probabilistic

Fix:
- Use deterministic enforcement
- `PreToolUse` hook in `settings.json`
- `exit code 2` = block

### Exam Pattern

- Missing team convention → scope issue
- Ignored hard rule → enforcement issue
