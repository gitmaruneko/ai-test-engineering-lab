# Agent SDK

## Key Points

- Claude Agent SDK handles the agent loop, tools, context management, and permissions.
- The developer provides the goal, available tools, and constraints.
- The agent follows a Gather → Act → Verify → Repeat loop.
- Hard requirements should use hooks or guardrails.

## Exam Cues

- Standard agent + no need to manually build tool loop → Agent SDK
- SHOULD → Prompt
- MUST / ALWAYS / NEVER → Hook / Guardrail
- Agent SDK supports Anthropic and cloud-provider authentication.

## SDK vs Custom Loop

- Use the Agent SDK for standard agents.
- The SDK already provides the agent loop, built-in tools, context management,
  and permissions.
- Hand-writing the loop for a standard agent is usually over-engineering.
- Use a custom loop when the SDK does not expose the required control.

### Exam Cue

- Standard agent → Agent SDK
- Need custom low-level control → Custom loop

### Connection to Agentic Loop

The Agent SDK internally runs the same `stop_reason`-based loop covered in
Concept 3.

`query()` hides the low-level loop, but the underlying process is still:

Claude → inspect `stop_reason` → run tool → return tool result → repeat
