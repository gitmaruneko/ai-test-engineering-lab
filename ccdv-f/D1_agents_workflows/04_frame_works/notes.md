## Frameworks — LangGraph, Strands & PydanticAI

### Core Mapping

| Framework  | Best Fit                                             |
| ---------- | ---------------------------------------------------- |
| LangGraph  | Long-running, stateful agents with durable execution |
| Strands    | AWS-native, model-driven agents                      |
| PydanticAI | Type-safe Python agents with strong validation       |

### LangGraph

Graph-based state machine built around:

- State
- Nodes
- Edges

Best for:

- Long-running agents
- Stateful workflows
- Durable execution / resume after failure
- Human-in-the-loop
- Memory
- Mixing deterministic and model-driven steps

> LangGraph = stateful graph orchestration

### Strands

AWS-native, model-driven agent SDK.

Agent = Model + System Prompt + Tools

Features:

- Python / TypeScript
- `@tool`
- MCP
- Multi-agent patterns
- AWS integration
- OpenTelemetry observability

> Strands = AWS-native agent framework

### PydanticAI

Type-safe, model-agnostic Python framework.

Features:

- Pydantic validation
- Structured outputs
- Tools
- MCP
- Evals
- Logfire observability

> PydanticAI = type-safe agents

### Exam Cues

- Long-running + stateful + resume → LangGraph
- Human-in-the-loop + durable execution → LangGraph
- AWS-native / AWS integration → Strands
- Type safety / validation → PydanticAI
- Structured output with Pydantic schemas → PydanticAI

> Learn the constraint-to-framework mapping, not the implementation details.

### The Decision Table

| The constraint says…                                           | → Choose            | Why                                                               |
| --------------------------------------------------------------- | -------------------- | ----------------------------------------------------------------- |
| "conditional branching, state rollback, auditable control flow" | **LangGraph**  | Graph state machine with durable execution and human-in-the-loop  |
| "AWS-native, managed scaling and lifecycle"                     | **Strands**    | Model-driven SDK with first-class AWS integration & observability |
| "every input/output must be schema-validated"                   | **PydanticAI** | Type-safe by design — validation moves bugs to write-time        |



### Reading Checkpoint

1. Which framework maps to "graph state machine with rollback"?
   LangGraph — graph-based state machine, durable execution, rollback/resume, auditable control flow.
2. Which framework is the AWS-native choice, and why?
   **Strands** , because it provides first-class AWS integration and observability.
   Strands = AWS-native

3. When is PydanticAI the right pick?
   When inputs and outputs must follow a strict schema and be validated.specific input\ output
4. What do all three frameworks have in common (licensing, model support)?
   All three are open-source and model-agnostic.


### Context Window Management

Long-running agents can exceed context limits.

Strategies:

- Progressive summarisation

  - Compress older turns
  - Preserve exact values such as IDs, amounts, and versions
- `/compact`

  - Claude Code's built-in context compaction
  - Keeps important facts while reducing context size
- Scratchpad files

  - Store intermediate results outside the context window
  - Read them back when needed
- Memory via tools

  - Store and retrieve important facts across turns

> Compress what can be summarized.
> Externalize what should be stored and retrieved later.
