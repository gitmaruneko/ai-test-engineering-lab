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

## Resources

### Claude Cookbooks

- `anthropics/claude-cookbooks`
- `patterns/agents/basic_workflows.ipynb`

### Video

- [How We Build Effective Agents — Barry Zhang, Anthropic](https://www.youtube.com/watch?v=D7_ipDqhtwk)

---

### Self-Check

After completing this section, I should be able to answer:

- [ ] State the one-line difference between a workflow and an agent.
- [ ] Name the workflow patterns covered in the course and give one use case for each.
- [ ] Explain why Anthropic advises developers to **start simple**.
- [ ] Explain when the additional cost and latency of an agent become worthwhile.


## 2. Agent SDK

### SDK & Construction

### SDK vs Custom Loop


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
