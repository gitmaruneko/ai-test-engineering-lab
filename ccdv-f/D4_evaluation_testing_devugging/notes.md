# Domain 4 — Evaluation, Testing & Debugging

## 1. Error Classification

### 4 Error Types

| Type | Origin | Typical Examples | Fix |
|---|---|---|---|
| Tool Error | External tool / API failure | DB timeout, API 500, service down, 429 | Retry with backoff, fallback, `is_error: true` |
| Reasoning Error | Model logic / judgment | Wrong calculation, hallucination, wrong tool selected | Improve prompt, examples, criteria |
| Environment Error | Runtime / infrastructure | OOM, disk full, permission denied | Fix infrastructure |
| Integration Error | Your code / API wiring | Bad message format, missing `tool_use_id`, parsing bug | Fix integration code |

### HTTP Status Rules

- `400 / 401 / 403 / 404`
  - Permanent/request-side problems
  - Fix the request / credentials / permission
  - **Do NOT retry**

- `429`
  - Rate limit
  - Transient
  - **Retry with exponential backoff**
  - Honor `retry-after`

- `500 / 504 / 529`
  - Server-side / timeout / overload
  - **Retry with exponential backoff**

### Transient Error

Transient = temporary failure that may recover later.

Examples:
- 429
- timeout
- network error
- 500 / 504 / 529

→ Retry with backoff

### `is_error: true`

Tool failures must be explicitly marked:

```json
{
  "type": "tool_result",
  "tool_use_id": "toolu_123",
  "content": "DB connection timeout",
  "is_error": true
}
```

Important:

- Error text alone is NOT enough
- Without `is_error: true`, Claude may treat the error as normal content

### Swallowed Error

Wrong:

```json
{
  "items": []
}
```

when the real cause was a DB timeout.

This incorrectly looks like:

> Query succeeded, but there were zero results.

Correct:

```text
Tool failure
→ `is_error: true`
→ classify as transient if appropriate
→ retry/recover
```

> Never disguise a failure as an empty success.

---

# 2. Trace Analysis

## `stop_reason`

First thing to inspect in an agent trace.

| stop_reason | Meaning |
|---|---|
| `end_turn` | Claude finished naturally |
| `tool_use` | Mid-loop; Claude expects a tool result |
| `max_tokens` | Output was truncated |
| `pause_turn` | Server-tool loop paused |
| `refusal` | Model declined the request |

Important:

> `tool_use` ≠ finished

If:

```text
stop_reason = tool_use
```

the application must:

1. Execute the tool
2. Return `tool_result`
3. Call Claude again

---

## `tool_use_id` Linking

Each tool call has an ID:

```text
tool_use.id = toolu_123
```

The result must reference the same ID:

```text
tool_result.tool_use_id = toolu_123
```

Must match exactly.

Wrong:

```text
tool_use.id = toolu_01
tool_result.tool_use_id = toolu_02
```

→ integration error / HTTP 400

### Tool Round Trip

```text
user
→ assistant (tool_use)
→ user (tool_result)
→ assistant (final response)
```

Because Messages API is stateless, the next API request must include:

- previous assistant `tool_use`
- new user `tool_result`

---

## Vanishing Result Bug

Symptom:

> Claude ignores a valid tool result.

First check:

1. Was the previous assistant `tool_use` message preserved?
2. Does `tool_result.tool_use_id` match `tool_use.id`?
3. Is the message history correctly assembled?

Typical cause:

```text
tool_result sent
BUT previous assistant tool_use was omitted
```

→ integration bug

---

## Runaway Loop

Symptom:

> 50+ turns, every turn is `stop_reason = tool_use`, never finishes.

Likely cause:

```text
tool_choice = "any"
```

`any` forces a tool call every turn.

Prefer:

```text
tool_choice = "auto"
```

Also define clear completion criteria.

### Repeated `max_tokens`

If every turn ends with:

```text
stop_reason = max_tokens
```

→ output is being truncated

Fix:
- increase `max_tokens`
- reduce input/context

---

## Trace Debugging Rule

Read chronologically.

Find:

> **the first turn where behavior diverges from expected**

Do NOT only debug the last wrong answer.

### Trace Checklist

Check:

- `stop_reason`
- tool results / `is_error`
- `tool_use_id`
- message role/order
- context accumulation
- reasoning drift

### Reasoning Drift

Reasoning drift = model gradually changes direction across turns even though the technical integration is working.

Example:

```text
Turn 1 → investigating reboot failure
Turn 2 → still relevant
Turn 3 → distracted by minor warning
Turn 4 → follows wrong hypothesis
Turn 5 → completely off original goal
```

---

# 3. Origin Isolation

## Console Replay Test

Goal:

> Determine whether the bug comes from the model/prompt or integration code.

Steps:

1. Log the exact production request
   - model
   - messages
   - tools

2. Replay the SAME request in Anthropic Console

3. Compare results

### Decision

```text
Same failure in Console
→ Model / Prompt issue

Console works correctly
→ Integration Code issue
```

Console replay removes your application code from the equation.

---

## Common Integration Bugs

- Dropping assistant `tool_use` message
- `tool_use_id` mismatch
- Invalid message/role ordering
- Truncated tool results
- Bad JSON parsing
- Application modifies request/response

### Strong Integration Bug Signals

- HTTP 400
- `tool_use_id not found`
- Console works, production fails

---

## Syntax vs Semantic Errors

### Syntax Error

Format is invalid.

Examples:
- malformed JSON
- missing brace
- wrong field type

Fix:
- structured output
- JSON mode
- tool/schema enforcement

### Semantic Error

Format is valid, but value/meaning is wrong.

Example:

```json
{
  "amount": 150
}
```

when invoice says:

```text
$1,500
```

The JSON is valid, but the value is wrong.

Fix:
- improve prompt
- clearer field descriptions
- field-level validation
- cross-check source data

> Structured Output guarantees FORMAT, not correctness.

### Key Rule

```text
Schema-valid ≠ accurate
```

---

## Wrong Tool Selected

Wrong tool choice does NOT automatically mean model incompetence.

Check first:

- tool name clarity
- tool description clarity
- parameter descriptions
- overlap between tools

Example:

Bad:

```text
get_user → lookup customer data
get_order → lookup customer data
```

Better:

```text
get_user → retrieve user profile by user_id
get_order → retrieve order details by order_id
```

> Wrong tool selection is often a tool-definition problem.

---

# 4. Recovery Strategies

## Recovery Decision Tree

### Retry with Backoff

Use for transient failures:

- 429
- timeout
- network error
- 500
- 504
- 529

Example backoff:

```text
1s → 2s → 4s → 8s
```

Do not retry immediately in a tight loop.

---

## Graceful Degradation

Use when part of the system still works.

Example:

```text
Search tool → works
Database tool → down
```

Instead of failing the entire request:

```text
Return search results
+ clearly report DB unavailable
```

> Partial failure → return partial value safely.

---

## Escalate to Human

Use when failure is persistent or cannot be solved automatically.

Examples:

- capability gap
- policy ambiguity
- no available tool
- repeated unrecoverable failure

Handoff should include:

- context
- partial results
- failure reason
- recommendation / next step

---

## Model Fallback

Use when API/model is persistently overloaded.

Example:

```text
529 sustained overload
→ consider fallback to another available model
```

---

## Recovery Summary

```text
Transient
→ Retry

Partial persistent failure
→ Graceful degradation

Capability gap / persistent failure
→ Escalate

Reasoning error
→ Fix prompt + Eval

Integration error
→ Fix code + Tests
```

---

# 5. Eval Methodology

## SMART Criteria

Success criteria should be:

- specific
- measurable

Good:

```text
F1 ≥ 0.85 on 10,000 samples
```

Bad:

```text
Classify well
```

---

## Grading Hierarchy

Prefer the cheapest reliable grader:

1. Code-based grading
2. LLM-as-judge
3. Human grading

### Code-based

Examples:
- exact match
- regex
- string match

Fast, cheap, deterministic.

### LLM-as-Judge

Use when output is subjective or flexible.

Examples:
- relevance
- tone
- summary quality

### Human Grading

Most expensive and slowest.

Use for:
- expert review
- high-risk cases
- gold-standard evaluation

---

## Eval Structure

A basic eval contains:

```text
input
output
expected
score
```

Example:

```text
input: "This product is amazing!"
output: "positive"
expected: "positive"
score: 1.0
```

---

## Quality Dimensions

Possible eval dimensions:

- task fidelity
- consistency
- relevance
- tone
- privacy
- context use
- latency
- price

---

# 6. Regression Testing

## Full Suite Rule

Every behavior-changing update must run the **full eval suite**.

Do NOT test only the cases you intended to fix.

Example:

```text
Prompt change fixes 3 failing cases
BUT breaks 2 previously passing cases
```

→ Regression

→ Reject / rollback the change

Even if:

```text
Average score improves
```

regressions still matter.

### Regression Cases

Regression cases = previously fixed bugs kept permanently in the eval suite.

---

## Eval Suite Should Include

- happy paths
- edge cases
- error handling
- adversarial inputs
- regression cases

Applies to changes in:

- prompts
- tool definitions
- system instructions
- model/configuration

> Every change → run the full suite.

---

# 7. Standard Debug Workflow

For a production agent returning incorrect results:

```text
1. Reproduce
2. Trace
3. Isolate
4. Fix
5. Full Eval
```

### 1. Reproduce
Create a minimal reproducible case.

### 2. Trace
Find the first failing turn.

### 3. Isolate
Use Console Replay to identify:

```text
Model/Prompt vs Integration
```

### 4. Fix
Fix the correct layer:

- prompt
- tool definition
- code
- infrastructure

### 5. Full Eval
Verify:
- original failure fixed
- no regressions introduced

---

# Exam Shortcuts

```text
400/401/403/404
→ Fix, don't retry

429
→ Rate limit
→ Backoff + retry

500/504/529
→ Retry with backoff

Tool failure
→ is_error: true

Claude ignores tool result
→ Check message history + tool_use_id

50+ tool calls
→ Check tool_choice="any"

Repeated max_tokens
→ Output truncation

Console correct, production wrong
→ Integration bug

Console reproduces same failure
→ Model / Prompt issue

Valid JSON, wrong value
→ Semantic error

Wrong tool selected
→ Check tool definition first

Partial failure
→ Graceful degradation

Capability gap
→ Escalate

Any behavior change
→ Run full eval suite

Debug workflow
→ Reproduce → Trace → Isolate → Fix → Eval
```
