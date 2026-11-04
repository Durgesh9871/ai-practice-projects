from langchain_core.messages import ToolMessage, AIMessage
from agent.graphstate import InvestigationGraphState


def observation_node(state: InvestigationGraphState):

    messages = state["messages"]
    observations = []

    # Step 1: Collect all latest ToolMessages
    tool_messages = []

    for msg in reversed(messages):

        if isinstance(msg, ToolMessage):
            tool_messages.append(msg)

        else:
            break

    tool_messages.reverse()

    if not tool_messages:
        return {"tool_observation": []}

    # Step 2: Find the AIMessage before these ToolMessages
    request_message = messages[
        len(messages) - len(tool_messages) - 1
    ]

    if not isinstance(request_message, AIMessage):
        return {"tool_observation": []}

    # Step 3: Match every ToolMessage with its tool call
    for tool_msg in tool_messages:

        for tool_call in request_message.tool_calls:

            if tool_call["id"] == tool_msg.tool_call_id:

                observations.append({

                    "tool_name": tool_call["name"],

                    "tool_call_id": tool_call["id"],

                    "arguments": tool_call["args"],

                    "content": str(tool_msg.content)[:500]

                })

                break

    return {
        "tool_observation": observations
    }