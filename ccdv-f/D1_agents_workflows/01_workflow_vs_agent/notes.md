# Domain 1 — Agents & Workflows

> Workflow uses predefined execution paths, while an agent determines the next
> action dynamically from intermediate results.

## Contents

- [1. Workflow vs Agent](#1-workflow-vs-agent)
  - [Core Distinction](#core-distinction)
  - [Exam Cues](#exam-cues)
  - [Decision Criteria](#decision-criteria)
  - [Firmware Testing Examples](#firmware-testing-examples)
  - [Quick Decision Rule](#quick-decision-rule)
  - [Reference Implementation — Claude Cookbooks](#reference-implementation--claude-cookbooks)
- [Labs](#labs)
- [References](#references)

## 1. Workflow vs Agent

### Core Distinction

The key difference between a workflow and an agent is **who determines the
execution path**.

| Type | Execution Path | Decision Authority |
| --- | --- | --- |
| **Workflow** | Predefined | Code decides |
| **Agent** | Dynamic | Claude decides based on intermediate results |

In short:

> **Workflow = predefined path → code decides**
>
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
| **Path predictability** | Known at design time | Depends on results |
| **Decision authority** | Code decides | Claude decides |
| **Auditability** | Easier to trace | Harder to trace |
| **Cost predictability** | Relatively predictable | Varies by tool calls |
| **Complexity** | Well-defined steps | Open-ended tasks |

---

### Firmware Testing Examples

#### Example 1 — Workflow

##### Workflow Requirement

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

##### Agent Requirement

Determine the possible root cause of a test failure and decide what additional
information should be investigated based on the evidence discovered.

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

The `basic_workflows.ipynb` notebook demonstrates several workflow
patterns.

#### Prompt Chaining

Sequential LLM calls where the output of one step becomes the input of the
next step.

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

The important distinction is whether the **overall architecture and available
execution paths are predetermined**.

In an agent:

> The next actions can be dynamically determined from intermediate results.

---

#### Resources

- Repository: `anthropics/claude-cookbooks`
- Notebook: `patterns/agents/basic_workflows.ipynb`
- Video: [How We Build Effective Agents — Barry Zhang][effective-agents]

---

#### Self-Check

I should be able to answer:

- [ ] What is the one-line difference between Workflow and Agent?
- [ ] What are the five workflow patterns?
- [ ] Why is Routing still a workflow?
- [ ] What is the difference between Routing and Orchestrator-Workers?
- [ ] What is the difference between Prompt Chaining and Evaluator-Optimizer?
- [ ] Why does parallel execution not automatically mean multi-agent?
- [ ] Why should the simplest reliable architecture be preferred?

## Labs

### Lab 1 — Workflow vs Agent

See [01_path.py](01_path.py) and [02_sdk_practice.py](02_sdk_practice.py).

## References

- [Anthropic — Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)
- [Claude Cookbooks — Basic Multi-LLM Workflows](https://github.com/anthropics/claude-cookbooks/blob/main/patterns/agents/)

[effective-agents]: https://www.youtube.com/watch?v=D7_ipDqhtwk
