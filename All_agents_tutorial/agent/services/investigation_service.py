from uuid import uuid4

from langchain_core.messages import HumanMessage

from agent.graph import build_graph
from agent.persistence.repository import (
    complete_run,
    create_run,
    fail_run,
    save_message,
)




def execute_investigation(
    objective: str,
    analytics_connection,
    thread_id: str | None = None,
) -> dict:
    current_thread_id = thread_id or str(uuid4())

    run = create_run(
        thread_id=current_thread_id,
        objective=objective,
    )

    save_message(
        run_id=run.run_id,
        role="user",
        content=objective,
    )

    graph = build_graph(analytics_connection)

    initial_state = {
        "messages": [HumanMessage(content=objective)],
        "hypotheses": [],
        "findings": [],
        "objective": objective,
        "tool_calls": 0,
        "step_count": 0,
        "is_finished": False,
        "final_report": "",
        "tool_observation": [],
        "completion_valid": False,
        "completion_feedback": "",
        "completion_attempts": 0,
        "sql_attempts": [],
        "sql_error_count": 0,
        "last_sql_error": "",
    }

    try:
        final_state = graph.invoke(initial_state)

        final_report = final_state["final_report"]

        save_message(
            run_id=run.run_id,
            role="assistant",
            content=final_report,
        )

        complete_run(
            run_id=run.run_id,
            final_report=final_report,
        )

        return {
            "run_id": run.run_id,
            "thread_id": current_thread_id,
            "status": "completed",
            "final_report": final_report,
            "state": final_state,
        }

    except Exception as error:
        fail_run(
            run_id=run.run_id,
            error_message=str(error),
        )

        raise