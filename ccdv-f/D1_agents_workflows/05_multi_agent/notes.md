## Multi-Agent & Context Isolation

### Core Idea

A multi-agent system uses multiple LLM instances with separate conversation contexts, coordinated through code.

Common pattern:

> Orchestrator → Subagents / Workers

### Context Isolation

Subagents do not automatically inherit the coordinator's conversation history.

The lead agent must explicitly pass:

- Task
- Relevant context
- Required data
- Constraints

> No shared memory by default.

### Why Multi-Agent Helps

Use multi-agent systems when there is:

1. **Context pollution**

   - One context becomes too large or noisy.
2. **Parallelism**

   - Independent subtasks can run concurrently.
3. **Specialisation**

   - Different prompts, tools, or expertise improve performance.

### Costs

Multi-agent systems use more:

- Tokens
- Model calls
- Latency
- Orchestration logic

Always ask:

> Can a well-prompted single agent solve this?

### Exam Cues

- Separate context windows → Multi-agent
- Parallel independent research → Multi-agent
- Specialist tools/prompts → Multi-agent
- Simple task → Prefer single agent
- Subagent does not inherit lead context → Pass context explicitly


### Mastery Check

I understand this section if I can explain:

- Why a single agent should be the default.
- Why every extra agent adds coordination cost and another failure point.
- Why missing scope usually points to coordinator decomposition.
- Why missing depth may point to a worker/subagent.
- Why subagents do not inherit coordinator history automatically.
- The three valid reasons to use multi-agent:
  - Context pollution
  - Parallelism
  - Specialisation
