from langgraph.graph import StateGraph, MessagesState, START, END


from typing import TypedDict
from langgraph.graph import StateGraph, START, END


# --------------------------------------------------
# Graph
#
#                  ┌→ analyze_bmc  ──┐
# START            │                 │
#   ↓              │                 │
# classify_failure ┼→ analyze_bios ──┼→ END
#                  │                 │
#                  └→ analyze_gpu  ──┘
# --------------------------------------------------


# State = graph 執行過程中攜帶的資料
class FailureState(TypedDict):
    log: str
    component: str
    result: str


# Node 1:
# 根據 log 判斷 failure 屬於哪個 component
def classify_failure(state: FailureState):

    log = state["log"]

    if "BMC" in log:
        component = "BMC"

    elif "BIOS" in log:
        component = "BIOS"

    elif "GPU" in log:
        component = "GPU"

    else:
        component = "UNKNOWN"

    print(f"[classify_failure] component = {component}")

    return {
        "component": component
    }


# Node 2A
def analyze_bmc(state: FailureState):

    print("[analyze_bmc] running...")

    return {
        "result": "BMC failure detected"
    }


# Node 2B
def analyze_bios(state: FailureState):

    print("[analyze_bios] running...")

    return {
        "result": "BIOS failure detected"
    }


# Node 2C
def analyze_gpu(state: FailureState):

    print("[analyze_gpu] running...")

    return {
        "result": "GPU failure detected"
    }


# --------------------------------------------------
# Routing function
#
# 這個 function 不修改 state。
# 它只負責告訴 LangGraph：
#
# 下一個 Node 要走哪裡？
# --------------------------------------------------

def route_failure(state: FailureState):

    component = state["component"]

    if component == "BMC":
        return "analyze_bmc"

    elif component == "BIOS":
        return "analyze_bios"

    elif component == "GPU":
        return "analyze_gpu"

    return END


# --------------------------------------------------
# Build Graph
# --------------------------------------------------

graph = StateGraph(FailureState)


# Add Nodes
graph.add_node("classify_failure", classify_failure)
graph.add_node("analyze_bmc", analyze_bmc)
graph.add_node("analyze_bios", analyze_bios)
graph.add_node("analyze_gpu", analyze_gpu)


# START → classify_failure
graph.add_edge(
    START,
    "classify_failure"
)


# classify_failure
#        ↓
# route_failure()
#        ↓
# BMC / BIOS / GPU
graph.add_conditional_edges(
    "classify_failure",
    route_failure,
)


# Analysis Nodes → END
graph.add_edge("analyze_bmc", END)
graph.add_edge("analyze_bios", END)
graph.add_edge("analyze_gpu", END)


# Compile
graph = graph.compile()


# --------------------------------------------------
# Run
# --------------------------------------------------

result = graph.invoke({
    "log": "BMC watchdog timeout",
    "component": "",
    "result": ""
})


print("\nFinal State:")
print(result)


# # https://docs.langchain.com/oss/python/langgraph/overview

# #                  ┌→ analyze_bmc
# # START
# #   ↓              │
# # classify_failure ┼→ analyze_bios
# #                  │
# #                  └→ analyze_gpu
# #                        ↓
# #                       END


# def analyze_bmc(state: MessagesState):
#     return {
#         "messages": [
#             {
#                 "role": "tool",
#                 "content": "hello BMC"
#             }
#         ]
#     }

# def analyze_bios(state: MessagesState):
#     return {
#         "messages": [
#             {
#                 "role": "tool",
#                 "content": "hello BIOS"
#             }
#         ]
#     }

# def analyze_gpu(state: MessagesState):
#     return {
#         "messages": [
#             {
#                 "role": "tool",
#                 "content": "hello GPU"
#             }
#         ]
#     }

# def classify_failure(state: MessagesState):
#     if "BMC" in state.messages[0].content:
#         return {
#             "next_node": "analyze_bmc"  
#         }
#     if "BIOS" in state.messages[0].content:
#         return {
#             "next_node": "analyze_bios"
#         }
#     if "GPU" in state.messages[0].content:
#         return {
#             "next_node": "analyze_gpu"
#         }



# graph = StateGraph(MessagesState)

# # create a Node named "classify_failure" and call Python function classify_failure()。
# graph.add_node("classify_failure", classify_failure)

# graph.add_edge(START, "classify_failure")
# graph.add_edge("classify_failure", END)

# graph = graph.compile()


# result = graph.invoke({
#     "messages": [
#         {
#             "role": "tool",
#             "content": ""
#         }
#     ]
# })

# print(result)