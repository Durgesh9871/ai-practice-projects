from agent.graphstate import InvestigationGraphState
from langchain_core.messages import AIMessage
from agent.tool_policy import DATA_TOOL_NAMES

def track_tool_usage(state:InvestigationGraphState)->InvestigationGraphState:
    

    # tool_calls = len(state["messages"][-1].tool_calls) if state["messages"][-1].tool_calls else 0
    latest_msg = state["messages"][-1]

    tool_calls = 0


    for tool_call in latest_msg.tool_calls:
        if tool_call["name"] in DATA_TOOL_NAMES:
            tool_calls += 1
        

    # if isinstance(latest_msg, AIMessage) and latest_msg.tool_calls:
    #     tool_calls = len(latest_msg.tool_calls)


    return {
        "tool_calls": state["tool_calls"] + tool_calls,
    }
