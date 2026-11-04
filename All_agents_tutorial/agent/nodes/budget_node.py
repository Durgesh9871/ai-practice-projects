from agent.graphstate import InvestigationGraphState
from langchain_core.messages import AIMessage

def track_tool_usage(state:InvestigationGraphState)->InvestigationGraphState:
    

    # tool_calls = len(state["messages"][-1].tool_calls) if state["messages"][-1].tool_calls else 0
    latest_msg = state["messages"][-1]

    tool_calls = 0

    if isinstance(latest_msg, AIMessage) and latest_msg.tool_calls:
        tool_calls = len(latest_msg.tool_calls)
    return {
        "tool_calls": state["tool_calls"] + tool_calls,
    }
