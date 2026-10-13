import asyncio
from dataclasses import dataclass


@dataclass
class MockMessage:
    type: str
    content: str


class MockClaudeAgentOptions:
    def __init__(self, allowed_tools=None):
        self.allowed_tools = allowed_tools or []


async def mock_query(prompt: str, options=None):
    """
    Mock version of Claude Agent SDK query().

    - No Claude login required
    - No API key required
    - No real Claude API call
    - Simulates an agent loop
    """

    allowed_tools = options.allowed_tools if options else []

    yield MockMessage(
        type="user_prompt",
        content=f"Goal received: {prompt}"
    )

    yield MockMessage(
        type="thinking",
        content="I need to inspect the task and decide what to do next."
    )

    if "Read" in allowed_tools:
        yield MockMessage(
            type="tool_use",
            content="Using Read tool to inspect auth.py"
        )

        yield MockMessage(
            type="tool_result",
            content="Found a mock authentication bug in auth.py."
        )

    if "Edit" in allowed_tools:
        yield MockMessage(
            type="tool_use",
            content="Using Edit tool to fix auth.py"
        )

        yield MockMessage(
            type="tool_result",
            content="auth.py updated successfully."
        )

    if "Bash" in allowed_tools:
        yield MockMessage(
            type="tool_use",
            content="Using Bash tool to run tests"
        )

        yield MockMessage(
            type="tool_result",
            content="All tests passed."
        )

    yield MockMessage(
        type="result",
        content="Task completed."
    )


async def main():
    options = MockClaudeAgentOptions(
        allowed_tools=["Read", "Edit", "Bash"]
    )

    async for message in mock_query(
        prompt="Find and fix the bug in auth.py",
        options=options,
    ):
        print(f"[{message.type}]")
        print(message.content)
        print()


if __name__ == "__main__":
    asyncio.run(main())


# ============================================================
# Explanation
# ============================================================
#
# This file simulates the basic usage style of Claude Agent SDK.
#
# Real SDK:
#
#   from claude_agent_sdk import query, ClaudeAgentOptions
#
# Mock version:
#
#   mock_query()
#   MockClaudeAgentOptions()
#
# The mock does NOT call Claude.
# It does NOT require login or an API key.
#
# The purpose is to understand the agent structure:
#
# Goal
#   ↓
# Agent decides what action to take
#   ↓
# Tool use
#   ↓
# Tool result
#   ↓
# Agent continues
#   ↓
# Final result
#
# allowed_tools defines what the agent is allowed to use.
#
# Example:
#
#   allowed_tools=["Read", "Edit", "Bash"]
#
# means the simulated agent is allowed to:
#
# - Read files
# - Edit files
# - Run shell commands
#
# Important:
# This example only SIMULATES agent behaviour.
# The decisions are still hard-coded in Python.
#
# A real Claude Agent SDK agent would let Claude decide
# dynamically which tool to use and what to do next.
# ============================================================