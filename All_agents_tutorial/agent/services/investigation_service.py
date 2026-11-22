from uuid import uuid4

from langchain_core.messages import HumanMessage
from agent.config import setting
from agent.persistence.database import initialize_database

from langgraph.checkpoint.sqlite import SqliteSaver

from agent.graph import build_graph



def new_investigation_state(objective: str) -> dict:
    return {
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
        "conversation_summary": "",
        "summarized_message_count": 0,
    }


def follow_up_state(objective: str) -> dict:
    return {
        "messages": [HumanMessage(content=objective)],
        "objective": objective,
        "tool_calls": 0,
        "step_count": 0,
        "is_finished": False,
        "final_report": "",
        "completion_valid": False,
        "completion_feedback": "",
        "completion_attempts": 0,
        "sql_error_count": 0,
        "last_sql_error": "",
    }



# def execute_investigation(
#     objective: str,
#     analytics_connection,
#     thread_id: str | None = None,
# ) -> dict:
#     initialize_database()

#     current_thread_id = thread_id or str(uuid4())

#     run = create_run(
#         thread_id=current_thread_id,
#         objective=objective,
#         status="queued"
#     )

#     save_message(
#         run_id=run.run_id,
#         role="user",
#         content=objective,
#     )

#     config = {
#         "configurable": {
#             "thread_id": current_thread_id,
#         }
#     }



#     try:
#         with SqliteSaver.from_conn_string(str(setting.app_database_path)) as checkpointer:
#             graph = build_graph(analytics_connection, checkpointer=checkpointer)
#             previous_state = graph.get_state(config)

#             if previous_state and previous_state.values:
#                 graph_input = follow_up_state(objective)
#             else:
#                 graph_input = new_investigation_state(objective)

#             final_state = graph.invoke(
#                 graph_input,
#                 config=config,
#             )   

#         final_report = final_state["final_report"]

#         save_message(
#             run_id=run.run_id,
#             role="assistant",
#             content=final_report,
#         )

#         complete_run(
#             run_id=run.run_id,
#             final_report=final_report,
#         )

#         return {
#             "run_id": run.run_id,
#             "thread_id": current_thread_id,
#             "status": "completed",
#             "final_report": final_report,
#             "state": final_state,
#         }

#     except Exception as error:
#         fail_run(
#             run_id=run.run_id,
#             error_message=str(error),
#         )

#         raise


import duckdb

from data.loader import DB_PATH
from agent.persistence.repository import (
    
    add_run_event,
    complete_run,
    create_run,
    fail_run,
    save_message,
    start_run,
)


def run_graph_investigation(
    run_id: str,
    thread_id: str,
    objective: str,
    analytics_connection: duckdb.DuckDBPyConnection,
) -> dict:
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    with SqliteSaver.from_conn_string(
        str(setting.app_database_path)
    ) as checkpointer:
        graph = build_graph(
            analytics_connection,
            checkpointer=checkpointer,
        )

        previous_state = graph.get_state(config)

        if previous_state and previous_state.values:
            graph_input = follow_up_state(objective)
        else:
            graph_input = new_investigation_state(objective)

        return graph.invoke(
            graph_input,
            config=config,
        )


def create_queued_investigation(
    objective: str,
    thread_id: str | None = None,
) -> dict:
    current_thread_id = thread_id or str(uuid4())

    run = create_run(
        thread_id=current_thread_id,
        objective=objective,
        status="queued",
    )

    add_run_event(
        run_id=run.run_id,
        event_type="queued",
        message="Your investigation is queued.",
    )

    save_message(
        run_id=run.run_id,
        role="user",
        content=objective,
    )

    return {
        "run_id": run.run_id,
        "thread_id": current_thread_id,
        "objective": objective,
        "status": "queued",
    }


def execute_queued_investigation(
    run_id: str,
    thread_id: str,
    objective: str,
) -> dict:
    analytics_connection = duckdb.connect(str(DB_PATH))

    try:
        start_run(run_id)

        add_run_event(
            run_id=run_id,
            event_type="started",
            message="Agent started analyzing your question.",
        )

        final_state = run_graph_investigation(
            run_id=run_id,
            thread_id=thread_id,
            objective=objective,
            analytics_connection=analytics_connection,
        )

        final_report = final_state["final_report"]

        save_message(
            run_id=run_id,
            role="assistant",
            content=final_report,
        )

        complete_run(
            run_id=run_id,
            final_report=final_report,
        )

        add_run_event(
            run_id=run_id,
            event_type="completed",
            message="Investigation completed.",
        )

        return {
            "run_id": run_id,
            "thread_id": thread_id,
            "status": "completed",
            "final_report": final_report,
        }

    # except Exception as error:
    #     fail_run(
    #         run_id=run_id,
    #         error_message=str(error),
    #     )
    #     raise

    finally:
        analytics_connection.close()