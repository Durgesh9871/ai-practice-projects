import json

from langchain_core.messages import ToolMessage

from agent.graphstate import InvestigationGraphState


def duplicate_sql_node(state: InvestigationGraphState) -> dict:
    latest_message = state["messages"][-1]
    tool_messages = []

    for tool_call in latest_message.tool_calls:
        if tool_call["name"] == "run_sql":
            content = {
                "success": False,
                "duplicate": True,
                "error": (
                    "Duplicate SQL blocked. This exact query already failed. "
                    "Use the previous error to produce a different corrected query."
                ),
            }
        else:
            content = {
                "success": False,
                "error": (
                    "Tool call cancelled because the batch contained "
                    "a duplicate failed SQL query."
                ),
            }

        tool_messages.append(
            ToolMessage(
                content=json.dumps(content),
                tool_call_id=tool_call["id"],
                name=tool_call["name"],
            )
        )

    return {"messages": tool_messages}