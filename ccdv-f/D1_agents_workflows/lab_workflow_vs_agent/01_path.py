from concurrent.futures import ThreadPoolExecutor


def extract_error(log: str) -> dict:
    """Prompt Chaining - Step 1"""
    result = {
        "component": None,
        "issue": None,
        "expected": None,
        "actual": None,
    }

    if "BMC firmware mismatch" in log:
        result["component"] = "BMC"
        result["issue"] = "firmware mismatch"

    for line in log.splitlines():
        if line.startswith("Expected BMC version:"):
            result["expected"] = line.split(":")[1].strip()

        if line.startswith("Actual BMC version:"):
            result["actual"] = line.split(":")[1].strip()

    return result


def classify_failure(error_info: dict) -> str:
    """Prompt Chaining - Step 2 / Routing classifier"""
    component = error_info.get("component")

    if component == "BMC":
        return "bmc"

    if component == "BIOS":
        return "bios"

    if component == "GPU":
        return "gpu"

    return "unknown"


def analyze_bmc(error_info: dict) -> str:
    return (
        f"BMC issue detected: {error_info['issue']}. "
        f"Expected {error_info['expected']}, "
        f"actual {error_info['actual']}."
    )


def analyze_bios(error_info: dict) -> str:
    return "BIOS failure detected."


def analyze_gpu(error_info: dict) -> str:
    return "GPU failure detected."


def analyze_unknown(error_info: dict) -> str:
    return "Unable to classify failure."


ROUTES = {
    "bmc": analyze_bmc,
    "bios": analyze_bios,
    "gpu": analyze_gpu,
    "unknown": analyze_unknown,
}


def route_failure(error_info: dict) -> str:
    """Routing workflow"""
    route = classify_failure(error_info)
    handler = ROUTES[route]

    return handler(error_info)


def collect_test_log() -> str:
    return "Test log collected"


def collect_sel() -> str:
    return "SEL collected"


def collect_fw_inventory() -> str:
    return "Firmware inventory collected"


def collect_failure_context() -> list[str]:
    """Parallelization workflow"""
    tasks = [
        collect_test_log,
        collect_sel,
        collect_fw_inventory,
    ]

    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(lambda task: task(), tasks))

    return results


def main():
    with open(".//test_failure.log", "r", encoding="utf-8") as file:
        log = file.read()

    print("=== Prompt Chaining ===")

    error_info = extract_error(log)
    print(error_info)

    classification = classify_failure(error_info)
    print(f"Classification: {classification}")

    print("\n=== Routing ===")

    analysis = route_failure(error_info)
    print(analysis)

    print("\n=== Parallelization ===")

    context = collect_failure_context()

    for item in context:
        print(item)


if __name__ == "__main__":
    main()


# ============================================================
# Lab Explanation
# ============================================================
#
# This lab demonstrates three workflow patterns:
#
# 1. Prompt Chaining
#
#    test_failure.log
#           ↓
#    extract_error()
#           ↓
#    classify_failure()
#
#    The output from one step becomes the input of the next step.
#    The execution order is predefined by code.
#
#
# 2. Routing
#
#    error_info
#        ↓
#    classify_failure()
#        ↓
#    ROUTES
#        ↓
#    BMC / BIOS / GPU / Unknown
#
#    The classifier selects one of several predefined routes.
#    Even if an LLM is later used for classification, this can still
#    remain a workflow because the available routes are predetermined.
#
#
# 3. Parallelization
#
#                  ┌─ collect_test_log()
#    Test Failure ─┼─ collect_sel()
#                  └─ collect_fw_inventory()
#
#    These tasks are independent, so they can run concurrently.
#    ThreadPoolExecutor is used here to demonstrate parallel execution.
#
#
# Why this is a workflow:
#
# - The overall execution structure is predefined.
# - The available routes are defined in code.
# - Code controls which steps can be executed.
# - The program does not dynamically invent new actions based on
#   intermediate results.
#
# Key takeaway:
#
# Workflow != no decision.
#
# A workflow may still include classification or routing decisions.
# The important distinction is whether the overall execution path
# and available actions are predetermined.
# ============================================================
