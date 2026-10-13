# Agentic Loop, Tool Use, and `stop_reason`

## Core Idea

`stop_reason` tells the application why Claude stopped and what the loop should
do next.

> Text is content; `stop_reason` is the control signal.

## Important `stop_reason` Values

- `end_turn`: The response is complete; stop the loop.
- `tool_use`: Execute the requested tool, return a `tool_result`, and continue.
- `max_tokens`: The response reached the token limit.
- `pause_turn`: Resume the server-tool loop.
- `refusal`: Claude declined the request.

## Tool Round-Trip

```text
Define tool
→ Claude returns tool_use
→ Execute tool
→ Return tool_result
→ Claude continues
```

## Review Questions

### 1. Why use `stop_reason` instead of judging from the response text?

The text content may be misleading. `stop_reason` is the authoritative control
signal that tells the application why Claude stopped and what to do next.

> Text is content; `stop_reason` is the control signal.

### 2. What should you do when `stop_reason` is `end_turn`?

Use the response and stop the loop.

```text
end_turn
→ Use the response
→ Stop
```

### 3. What should you do when `stop_reason` is `tool_use`?

Execute the requested tool, return a `tool_result` with the matching
`tool_use_id`, and continue the loop.

```text
tool_use
→ Execute the requested tool
→ Return the matching tool_result
→ Continue the loop
```

### 4. What is `tool_use_id` used for?

It correlates a `tool_result` with the exact `tool_use` request it answers.

### 5. What is the tool round-trip?

Define the tool, receive a `tool_use` request, execute the tool, return its
`tool_result`, and let Claude continue.

### 6. What is the difference between a client tool and a server tool?

- **Client tool:** Executed by your application or environment.
- **Server tool:** Executed by the tool provider's infrastructure.

## Errors and Anti-Patterns

- Do not infer completion from response text; use `stop_reason`.
- When handling `tool_use`, return a `tool_result` with the matching
  `tool_use_id`.
- Validate tool names and inputs before executing requests in a production
  application.
- Handle stop reasons other than `tool_use` and `end_turn` explicitly.
- If a tool fails, return an error result (for example, `is_error: true`) rather
  than presenting the failure as a successful result.

## Effective Context Engineering for AI Agents

### Core Principle

> Keep the smallest set of high-signal tokens needed for the task.

More context is not always better; long contexts can reduce attention and
retrieval quality.

### Key Techniques

- Just-in-time retrieval
- Progressive disclosure
- Compaction
- Structured note-taking
- Sub-agent isolation

### Error Recovery

Preserve relevant state, including:

- IDs
- Previous tool errors
- Retry count
- Important task state

> Keep the right context, not the most context.
