from langgraph.graph import StateGraph, MessagesState, START, END


# https://docs.langchain.com/oss/python/langgraph/overview

# START
#   ↓
# mock_llm
#   ↓
# END

def mock_llm(state: MessagesState):
    return {
        "messages": [
            {
                "role": "ai",
                "content": "hello world"
            }
        ]
    }


graph = StateGraph(MessagesState)

# create a Node named "mock_llm" and call Python function mock_llm()。
graph.add_node("mock_llm", mock_llm)

graph.add_edge(START, "mock_llm")
graph.add_edge("mock_llm", END)

graph = graph.compile()


result = graph.invoke({
    "messages": [
        {
            "role": "user",
            "content": "hi!"
        }
    ]
})

print(result)