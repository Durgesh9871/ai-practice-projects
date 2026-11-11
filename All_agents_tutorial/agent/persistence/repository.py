from datetime import datetime, timezone
from uuid import uuid4

from agent.persistence.database import get_app_database
from agent.persistence.model import InvestigationRun


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_run(
    thread_id: str,
    objective: str,
) -> InvestigationRun:
    run = InvestigationRun(
        run_id=str(uuid4()),
        thread_id=thread_id,
        objective=objective,
        status="running",
    )

    timestamp = utc_now()

    with get_app_database() as connection:
        connection.execute(
            """
            INSERT INTO investigation_runs (
                run_id,
                thread_id,
                objective,
                status,
                final_report,
                error_message,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run.run_id,
                run.thread_id,
                run.objective,
                run.status,
                run.final_report,
                run.error_message,
                timestamp,
                timestamp,
            ),
        )

    return run


def save_message(
    run_id: str,
    role: str,
    content: str,
) -> None:
    with get_app_database() as connection:
        connection.execute(
            """
            INSERT INTO chat_messages (
                message_id,
                run_id,
                role,
                content,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                run_id,
                role,
                content,
                utc_now(),
            ),
        )


def complete_run(
    run_id: str,
    final_report: str,
) -> None:
    with get_app_database() as connection:
        connection.execute(
            """
            UPDATE investigation_runs
            SET status = ?,
                final_report = ?,
                updated_at = ?
            WHERE run_id = ?
            """,
            (
                "completed",
                final_report,
                utc_now(),
                run_id,
            ),
        )


def fail_run(
    run_id: str,
    error_message: str,
) -> None:
    with get_app_database() as connection:
        connection.execute(
            """
            UPDATE investigation_runs
            SET status = ?,
                error_message = ?,
                updated_at = ?
            WHERE run_id = ?
            """,
            (
                "failed",
                error_message,
                utc_now(),
                run_id,
            ),
        )