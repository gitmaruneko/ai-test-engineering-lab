## Agentic Loop, Tool Use & stop_reason

### Core Idea

`stop_reason` tells the application why Claude stopped and what the loop should do next.

> Text = content
> `stop_reason` = control signal

### Important stop_reason Values

- `end_turn` → response is complete, stop the loop
- `tool_use` → execute the tool, return `tool_result`, continue
- `max_tokens` → token limit reached
- `pause_turn` → resume the server-tool loop
- `refusal` → Claude declined the request

### Tool Round-Trip

```text
Define tool
→ Claude returns tool_use
→ Execute tool
→ Return tool_result
→ Claude continues
```

### Review Questions

#### 1. Why should you use `stop_reason` instead of judging from the text content?

Because the text content may be misleading.

`stop_reason` is the authoritative control signal that tells the application why Claude stopped and what to do next.

> Text = content
> `stop_reason` = control signal

---

#### 2. What should you do when `stop_reason` is `end_turn`?

Use the response and stop the loop.

```text
end_turn
→ use response
→ stop
```

### 3. What should you do when stop_reason is tool_use?

Execute the requested tool, return a tool_result, then continue the loop.
tool_use
→ execute tool
→ return tool_result
→ continue

### 4. What is tool_use_id used for?

It matches a tool_result to the correct tool_use request.

tool_use_id = correlation ID

### 5.What is the Tool Round-Trip?

Define tool
→ Claude returns tool_use
→ Execute tool
→ Return tool_result
→ Claude continues

### 6. What is the difference between a Client Tool and a Server Tool?

Client Tool → executed in your application / environment

Server Tool → executed on Anthropic infrastructure


## Errors & Anti-Patterns

- Do not infer completion from response text; use `stop_reason` as the control signal.
- When handling `tool_use`, return a `tool_result` with the matching `tool_use_id`.
- Validate tool names and inputs before executing requests in a production application.
- Handle stop reasons other than `tool_use` and `end_turn` explicitly; this mock loop raises an error for unsupported reasons.
