"""CCDV-F Domain 1 Lab: a minimal mock agentic loop.

Run with:
    python lab_agentic_loop.py

This program uses only the Python standard library.  It does NOT call an API.
Instead, mock_model_response() stands in for a model so you can focus on the
control flow:

    tool_use -> run local tool -> tool_result -> model continues -> end_turn
"""

from typing import Any, Dict, List


# These are "client tools": they run in *our* Python program, not in a model.
def read_log() -> str:
    """Return a pretend firmware test log."""
    return "BOOT_104: BMC initialization timed out after 30 seconds."


def read_sel() -> str:
    """Return a pretend System Event Log (SEL) entry."""
    return "SEL: BMC watchdog event recorded during platform initialization."


TOOLS = {
    "read_log": read_log,
    "read_sel": read_sel,
}


def mock_model_response(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Return deterministic fake model responses based on prior tool results.

    In a real application, this function would call a model API.  The shape of
    the returned data and the loop below are the parts worth studying here.
    """
    tool_results = [
        block
        for message in messages
        if message["role"] == "user"
        # The first user message is plain text; tool results are a list of blocks.
        if isinstance(message.get("content"), list)
        for block in message["content"]
        if block.get("type") == "tool_result"
    ]

    if not tool_results:
        return {
            "stop_reason": "tool_use",
            "content": [{
                "type": "tool_use",
                "id": "toolu_read_log_001",
                "name": "read_log",
                "input": {},
            }],
        }

    # The second tool is optional: ask for the SEL only when the boot log points
    # to the BMC.  Our supplied mock log takes this branch.
    first_tool_output = tool_results[0]["content"]
    if len(tool_results) == 1 and "BMC" in first_tool_output:
        return {
            "stop_reason": "tool_use",
            "content": [{
                "type": "tool_use",
                "id": "toolu_read_sel_002",
                "name": "read_sel",
                "input": {},
            }],
        }

    # end_turn means the model is done: use this answer and leave the loop.
    return {
        "stop_reason": "end_turn",
        "content": [{
            "type": "text",
            "text": (
                "Diagnosis: the firmware test likely failed because the BMC "
                "timed out during initialization. The watchdog event in the "
                "SEL supports a BMC-side issue."
            ),
        }],
    }


def run_agent_loop() -> None:
    """Drive the model/tool round-trip until the authoritative stop signal ends it."""
    messages: List[Dict[str, Any]] = [
        {"role": "user", "content": "Check why the firmware test failed."}
    ]

    print("=== Mock firmware diagnostic agent ===\n")

    while True:
        response = mock_model_response(messages)
        stop_reason = response["stop_reason"]
        print(f"Model stop_reason: {stop_reason}")

        # Do not infer completion from the text. stop_reason is the control signal.
        if stop_reason == "end_turn":
            final_text = response["content"][0]["text"]
            print(f"\nFinal answer:\n{final_text}")
            break

        if stop_reason != "tool_use":
            raise RuntimeError(f"Unexpected stop_reason: {stop_reason}")

        # Save the assistant's tool request before returning its result.
        messages.append({"role": "assistant", "content": response["content"]})

        tool_result_blocks: List[Dict[str, str]] = []
        for tool_request in response["content"]:
            tool_name = tool_request["name"]
            tool_use_id = tool_request["id"]
            print(f"Tool request: {tool_name} (tool_use_id={tool_use_id})")

            # A production app should validate the tool name and input carefully.
            tool_output = TOOLS[tool_name]()
            print(f"Tool output:  {tool_output}\n")

            # tool_use_id is the correlation ID: it attaches this exact result to
            # this exact tool request, even when a response asks for many tools.
            tool_result_blocks.append({
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": tool_output,
            })

        # Send tool_result back as a user message, then let the model continue.
        messages.append({"role": "user", "content": tool_result_blocks})


if __name__ == "__main__":
    run_agent_loop()
