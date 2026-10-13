from pydantic import BaseModel, Field
from pydantic_ai import Agent


# ----------------------------------------
# Define the structured output schema
# ----------------------------------------

class FirmwareFailureResult(BaseModel):
    component: str
    severity: int = Field(ge=1, le=3)
    action: str


# ----------------------------------------
# Create an offline test agent
#
# "test" uses PydanticAI's TestModel,
# so no API key is required.
# ----------------------------------------

agent = Agent(
    "test",
    output_type=FirmwareFailureResult,
)


# ----------------------------------------
# Run the agent
# ----------------------------------------

result = agent.run_sync(
    """
    Analyze this firmware failure:

    BMC watchdog timeout detected during boot.

    Return:
    - component
    - severity from 1 to 5
    - recommended action
    """
)


# ----------------------------------------
# Access validated structured output
# ----------------------------------------

output = result.output

print("Validated Result:")
print(output)

print("\nFields:")
print("Component:", output.component)
print("Severity:", output.severity)
print("Action:", output.action)