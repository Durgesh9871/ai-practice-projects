import ast
import json

from langchain_core.messages import ToolMessage, AIMessage

from agent.graphstate import InvestigationGraphState
from agent.sql_utils import normalize_sql
from agent.tool_policy import DATA_TOOL_NAMES


def parse_tool_result(content) -> dict:
    if isinstance(content, dict):
        return content

    if not isinstance(content, str):
        return {}

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        try:
            parsed = ast.literal_eval(content)
            return parsed if isinstance(parsed, dict) else {}
        except (ValueError, SyntaxError):
            return {}


def observation_node(state: InvestigationGraphState) -> dict:
    messages = state["messages"]
    tool_messages = []

    for message in reversed(messages):
        if isinstance(message, ToolMessage):
            tool_messages.append(message)
        else:
            break

    tool_messages.reverse()

    if not tool_messages:
        return {"tool_observation": []}

    request_index = len(messages) - len(tool_messages) - 1
    request_message = messages[request_index]

    if not isinstance(request_message, AIMessage):
        return {"tool_observation": []}

    tool_calls_by_id = {
        call["id"]: call
        for call in request_message.tool_calls
    }

    observations = []
    sql_attempts = []

    sql_error_count = state.get("sql_error_count", 0)
    last_sql_error = state.get("last_sql_error", "")

    for tool_message in tool_messages:
        tool_call = tool_calls_by_id.get(tool_message.tool_call_id)

        if not tool_call:
            continue

        tool_name = tool_call["name"]

        # Hypothesis and finding tools are not raw data evidence.
        if tool_name not in DATA_TOOL_NAMES:
            continue

        observations.append({
            "tool_name": tool_name,
            "tool_call_id": tool_call["id"],
            "arguments": tool_call["args"],
            "content": str(tool_message.content)[:500],
        })

        if tool_name != "run_sql":
            continue

        result = parse_tool_result(tool_message.content)
        query = tool_call["args"].get("query", "")
        success = result.get("success") is True
        error = str(result.get("error", ""))

        sql_attempts.append({
            "query": query,
            "normalized_query": normalize_sql(query),
            "tool_call_id": tool_call["id"],
            "success": success,
            "error": error,
        })

        if success:
            # Successful repair ends the consecutive failure sequence.
            sql_error_count = 0
            last_sql_error = ""
        else:
            sql_error_count += 1
            last_sql_error = error or "SQL execution failed."

    updates = {
        "tool_observation": observations,
    }

    if sql_attempts:
        updates.update({
            "sql_attempts": sql_attempts,
            "sql_error_count": sql_error_count,
            "last_sql_error": last_sql_error,
        })

    return updates