from datetime import datetime, timezone
from uuid import uuid4

from agent.persistence.database import get_app_database
from agent.persistence.model import InvestigationRun


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()




def start_run(run_id: str) -> None:
    with get_app_database() as connection:
        connection.execute(
            """
            UPDATE investigation_runs
            SET status = ?,
                updated_at = ?
            WHERE run_id = ?
            """,
            (
                "running",
                utc_now(),
                run_id,
            ),
        )

def add_run_event(
    run_id: str,
    event_type: str,
    message: str,
) -> None:
    with get_app_database() as connection:
        next_sequence = connection.execute(
            """
            SELECT COALESCE(MAX(event_sequence), 0) + 1
            FROM investigation_events
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()[0]

        connection.execute(
            """
            INSERT INTO investigation_events (
                event_id,
                run_id,
                event_sequence,
                event_type,
                message,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                run_id,
                next_sequence,
                event_type,
                message,
                utc_now(),
            ),
        )


def get_run_events(run_id: str) -> list[dict]:
    with get_app_database() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM investigation_events
            WHERE run_id = ?
            ORDER BY event_sequence ASC
            """,
            (run_id,),
        ).fetchall()

    return [dict(row) for row in rows]

    

def create_run(
    thread_id: str,
    objective: str,
    status: str
) -> InvestigationRun:
    run = InvestigationRun(
        run_id=str(uuid4()),
        thread_id=thread_id,
        objective=objective,
        status=status,
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


def get_run(run_id: str) -> InvestigationRun | None:
    with get_app_database() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM investigation_runs
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()

        if not row:
            return None

        return dict(row)



def get_thread_runs(thread_id: str) -> list[dict]:
    with get_app_database() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM investigation_runs
            WHERE thread_id = ?
            ORDER BY created_at DESC
            """,
            (thread_id,),
        ).fetchall()

    return [dict(row) for row in rows]        


def get_run_messages(run_id: str) -> list[dict]:
    with get_app_database() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM chat_messages
            WHERE run_id = ?
            ORDER BY created_at DESC
            """,
            (run_id,),
        ).fetchall()

    return [dict(row) for row in rows]
