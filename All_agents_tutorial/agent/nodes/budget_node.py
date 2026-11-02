from agent.graphstate import InvestigationGraphState


def track_tool_usage(state:InvestigationGraphState)->InvestigationGraphState:
    

    tool_calls = len(state["messages"][-1].tool_calls) if state["messages"][-1].tool_calls else 0

    return {
        "tool_calls": state["tool_calls"] + tool_calls,
    }
