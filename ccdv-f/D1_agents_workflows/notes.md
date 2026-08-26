# Domain 1 — Agents & Workflows

> Workflow uses predefined execution paths, while an agent determines the next action dynamically from intermediate results.

## Contents

- [1. Workflow vs Agent](#1-workflow-vs-agent)
  - [Core Distinction](#core-distinction)
  - [Exam Cues](#exam-cues)
  - [Decision Criteria](#decision-criteria)
  - [Firmware Testing Examples](#firmware-testing-examples)
  - [Quick Decision Rule](#quick-decision-rule)
  - [Reference Implementation — Claude Cookbooks](#reference-implementation--claude-cookbooks)
- [2. Agent SDK](#2-agent-sdk)
  - [SDK & Construction](#sdk--construction)
  - [Firmware Example](#firmware-example)
  - [SDK vs Custom Loop](#sdk-vs-custom-loop)
  - [Claude Integration Options](#claude-integration-options)
  - [Checkpoint](#checkpoint)
  - [Resources](#resources)
- [3. Agentic Loop](#3-agentic-loop)
- [4. Frameworks](#4-frameworks)
- [5. Multi-Agent](#5-multi-agent)
- [Labs](#labs)
- [References](#references)

## 1. Workflow vs Agent

### Core Distinction

The key difference between a workflow and an agent is **who determines the execution path**.

| Type | Execution Path | Decision Authority |
| --- | --- | --- |
| **Workflow** | Predefined | Code decides |
| **Agent** | Dynamic | Claude decides based on intermediate results |

In short:

> **Workflow = predefined path → code decides**
> **Agent = dynamic path → Claude decides**

---

### Exam Cues

Common wording that may indicate which architecture to choose:

- `fixed`
- `predetermined`
- `same steps every time`
  → **Workflow**

- `depends on intermediate results`
- `depends on what Claude discovers`
- `cannot be determined in advance`
  → **Agent**

- `minimum viable architecture`
  → **Prefer the simpler design that satisfies the requirement**

A more capable or autonomous architecture is not automatically the better choice.

---

### Decision Criteria

| Criterion | Workflow | Agent |
| --- | --- | --- |
| **Path predictability** | Steps are known at design time | Steps depend on intermediate results |
| **Decision authority** | Code decides the next step | Claude decides the next step |
| **Auditability** | Easier to trace because code controls branches | Harder to trace because model decisions drive the path |
| **Cost predictability** | Token and tool usage are relatively predictable | Cost can vary depending on how many steps or tool calls are needed |
| **Complexity** | Best suited to a small number of well-defined steps | Suitable for open-ended tasks where steps cannot be predetermined |

---

### Firmware Testing Examples

#### Example 1 — Workflow

**Requirement**

After every test failure:

1. Collect the test log.
2. Collect SEL.
3. Collect firmware inventory.
4. Generate a report.

This should be implemented as a **workflow**.

Why:

- **Path:** Fixed
- **Decision authority:** Code
- **Auditability:** Easy
- **Cost:** Relatively predictable
- **Complexity:** Four clearly defined steps

```text
Test Fail
    ↓
Collect Log
    ↓
Collect SEL
    ↓
Collect FW Inventory
    ↓
Generate Report
```

---

#### Example 2 — Agent

**Requirement**

Determine the possible root cause of a test failure and decide what additional information should be investigated based on the evidence discovered.

This is more suitable for an **agent**.

Why:

- **Path:** Unknown in advance
- **Decision authority:** Claude
- **Auditability:** More difficult
- **Cost:** Variable
- **Complexity:** Open-ended

Example:

```text
Analyze Test Log
    ↓
Possible BMC issue
    ↓
Claude decides to inspect SEL
    ↓
Possible firmware mismatch
    ↓
Claude decides to inspect FW inventory
    ↓
Continue investigation as needed
```

---

### Quick Decision Rule

When deciding between a workflow and an agent, ask:

#### Q1. Can the steps be determined during application design?

**Yes**
→ Prefer a **Workflow**

**No**
→ Continue to Q2

#### Q2. Does Claude need to decide the next action based on intermediate results?

**Yes**
→ Consider an **Agent**

```text
Can the execution path be predefined?
        │
      Yes
        ↓
    Workflow

        │ No
        ↓

Does Claude need to determine
the next step dynamically?
        │
      Yes
        ↓
      Agent
```

---

### Reference Implementation — Claude Cookbooks

Repository:

`anthropics/claude-cookbooks`

Local setup:

```text
Clone / download claude-cookbooks
    ↓
Open with VS Code
    ↓
Install Jupyter support if executing notebooks locally
    ↓
Browse:
patterns/agents/basic_workflows.ipynb
```

The `basic_workflows.ipynb` notebook demonstrates several workflow patterns.

#### Prompt Chaining

Sequential LLM calls where the output of one step becomes the input of the next step.

```text
Input
  ↓
Step 1
  ↓
Step 2
  ↓
Step 3
  ↓
Output
```

Key points:

- Sequential steps
- Each LLM output becomes the next step's input
- Execution structure is predefined by code

Firmware example:

```text
Test Log
    ↓
Extract Errors
    ↓
Classify Component
    ↓
Summarize Failure
    ↓
Generate Report
```

---

#### Parallelization

Independent tasks are executed concurrently.

Key points:

- Useful when tasks do not depend on each other's results
- Can reduce overall latency
- The tasks to execute are still predefined by code

Firmware example:

```text
                 ┌─ Analyze Test Log
Test Failure ────┼─ Analyze SEL
                 └─ Analyze FW Inventory
                         ↓
                    Merge Results
```

> Parallel LLM calls do **not** automatically mean multi-agent.

---

#### Routing

The input is classified and sent to one of several predefined specialized paths.

```text
Input
    ↓
Classifier
    ↓
 ┌───────┬────────┬───────┐
 BMC    BIOS      GPU    Network
```

Key points:

- Claude may decide which route to select
- The available routes are defined in advance
- The architecture is still predetermined

Therefore, routing is still a **workflow**.

Firmware example:

```text
Failure Log
    ↓
Classify Failure
    ↓
 ┌─────────┬──────────┬─────────┐
 BMC       BIOS       GPU      Network
 ↓          ↓          ↓          ↓
BMC       BIOS       GPU       Network
Analyzer  Analyzer   Analyzer   Analyzer
```

---

#### Important Takeaway

Prompt chaining, parallelization, and routing are all **workflow patterns**.

> **Workflow does not mean that the LLM cannot make any decisions.**

For example, Claude may select a route during routing.

The important distinction is whether the **overall architecture and available execution paths are predetermined**.

In an agent:

> The next actions can be dynamically determined from intermediate results.

---

#### Resources
* Claude Cookbooks
    - `anthropics/claude-cookbooks`
    - `patterns/agents/basic_workflows.ipynb`

* Video
    - [How We Build Effective Agents — Barry Zhang, Anthropic](https://www.youtube.com/watch?v=D7_ipDqhtwk)

---

#### Self-Check

After completing this section, I should be able to answer:

- [ ] State the one-line difference between a workflow and an agent.
- [ ] Name the workflow patterns covered in the course and give one use case for each.
- [ ] Explain why Anthropic advises developers to **start simple**.
- [ ] Explain when the additional cost and latency of an agent become worthwhile.


## 2. Agent SDK

### SDK & Construction

- Agent SDK provides the agent loop:
  model → tool call → tool result → model → repeat.

- The developer provides:
  - Goal / prompt
  - Available tools
  - Permissions / constraints

- Claude determines the intermediate actions dynamically.

- Built-in general-purpose tools such as Read, Edit, and Bash
  allow the agent to operate more like a developer.

- Hard requirements should be enforced through deterministic
  mechanisms such as hooks, guardrails, or permissions rather
  than relying only on prompts.

- System prompt provides **probabilistic guidance**.
- Hooks / guardrails provide **deterministic enforcement**.
- If something MUST happen every time, do not rely only on the model remembering the instruction.

Exam cue:

- SHOULD → Prompt
- MUST / ALWAYS / NEVER → Hook or guardrail

#### Firmware Example

Goal: "Find the likely root cause of this firmware test failure."

Allowed tools:

- Read test log
- Read SEL
- Get firmware inventory
- Run diagnostic command

Possible agent loop:

```text
Test log
→ Claude suspects BMC
→ Read SEL
→ Claude suspects firmware mismatch
→ Get FW inventory
→ Verify version mismatch
→ Return root cause
```


### SDK vs Custom Loop

> **Important Reminder — What does "SDK" mean here?**
>
> The **Claude Agent SDK is not part of the Claude Desktop application**.
>
> It is a developer library installed inside your own project, for example:
>
> ```bash
> pip install claude-agent-sdk
> ```
>
> Then your Python application can use it:
>
> ```python
> from claude_agent_sdk import query
> ```
>
> Think of the difference as:
>
> - **Claude Desktop / Claude Code** → ready-to-use products
> - **Anthropic SDK** → library for calling the Claude API
> - **Claude Agent SDK** → library for building your own agent, with agent loop, tools, context management, and permissions
>
> **Key point:**
> Agent SDK = something I use **in my own code**, not something I operate inside the Claude desktop app.

#### Exam Cue

- Standard agent requirements → prefer Agent SDK
- Need low-level / custom control not exposed by SDK → custom loop
- Do not rebuild existing SDK infrastructure without a clear requirement

#### Cost Reminder

> Installing the Claude Agent SDK is free.
> Costs come from the model/API calls made while the agent is running.
> Because an agent may make multiple model calls, use controls such as
> `max_budget_usd` when cost predictability matters.

#### Claude Integration Options

- **Claude Code CLI**
  → Interactive terminal use.

- **Client SDK**
  → Direct API access; developer implements the tool loop.

- **Agent SDK**
  → Build an agent without implementing the tool loop yourself.

- **Managed Agents**
  → Hosted long-running / asynchronous agents; infrastructure managed for you.

#### Checkpoint

- Agent SDK = Loop + Tools + Context + Permissions

- `allowed_tools` = pre-approved tools

- Providers = Anthropic / Bedrock / Vertex / Foundry

- Custom loop = only when SDK does not expose the control you need

#### Resources

- [Build & deploy agents with the Claude Agent SDK](https://www.youtube.com/watch?v=jNpH_hOFvg4)
- [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview)
- [Building agents with the Claude Agent SDK](https://claude.com/blog/building-agents-with-the-claude-agent-sdk)
- [Claude Agent SDK for Python](https://github.com/anthropics/claude-agent-sdk-python)

## 3. Agentic Loop

### stop_reason & Tool Use

### Errors & Anti-Patterns


## 4. Frameworks

### LangGraph, Strands, Pydantic

### Matching the Constraint


## 5. Multi-Agent

### Orchestrator & Context

### When NOT to Multi-Agent


## Labs

### Lab 1 — Workflow vs Agent

See: `lab_workflow_vs_agent/`


## References

- [Anthropic — Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)
- [Claude Cookbooks — Basic Multi-LLM Workflows](https://github.com/anthropics/claude-cookbooks/blob/main/patterns/agents/)
