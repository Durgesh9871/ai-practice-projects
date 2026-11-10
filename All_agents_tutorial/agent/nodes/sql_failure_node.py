from langchain_core.messages import AIMessage

from agent.graphstate import InvestigationGraphState


def sql_failure_node(state: InvestigationGraphState) -> dict:
    message = AIMessage(
        content=(
            "The SQL investigation was stopped because the SQL retry "
            "limit was reached. The query could not be repaired safely. "
            f"Last SQL error: {state.get('last_sql_error', 'Unknown error')}"
        )
    )

    return {
        "messages": [message],
        "is_finished": True,
    }