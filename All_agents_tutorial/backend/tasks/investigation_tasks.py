from backend.worker.celery_app import celery_app


@celery_app.task(
    name="backend.tasks.execute_investigation",
    bind=True,
)
def execute_investigation_task(
    self,
    run_id: str,
    thread_id: str,
    objective: str,
) -> None:
    from agent.services.investigation_service import (
        execute_queued_investigation,
    )

    execute_queued_investigation(
        run_id=run_id,
        thread_id=thread_id,
        objective=objective,
    )