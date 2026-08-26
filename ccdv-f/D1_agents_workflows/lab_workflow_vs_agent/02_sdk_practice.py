import anyio

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
)


async def main():
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write"]
    )

    async for message in query(
        prompt="Create a file called hello.txt with 'Hello World' in it.",
        options=options,
    ):
        print(message)


anyio.run(main)
