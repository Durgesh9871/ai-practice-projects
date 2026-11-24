from backend.worker.celery_app import celery_app
from agent.persistence.repository import fail_run
from agent.services.investigation_service import execute_queued_investigation

from agent.persistence.repository import add_run_event, fail_run





def is_retryable_provider_error(error: Exception) -> bool:
    message = str(error).lower()

    retryable_markers = (
        "429",
        "resource_exhausted",
        "rate limit",
        "quota",
        "503",
        "service unavailable",
    )

    return any(marker in message for marker in retryable_markers)


@celery_app.task(
    name="backend.tasks.execute_investigation",
    bind=True,
    max_retries=3,
)
def execute_investigation_task(
    self,
    run_id: str,
    thread_id: str,
    objective: str,
) -> None:
    

    try:
        execute_queued_investigation(
            run_id=run_id,
            thread_id=thread_id,
            objective=objective,
        )

    except Exception as error:
        if (
            is_retryable_provider_error(error)
            and self.request.retries < self.max_retries
        ):
            delay_seconds = min(60, 10 * (2 ** self.request.retries))

            add_run_event(
                run_id=run_id,
                event_type="retry_scheduled",
                message="Temporary provider limit reached. Retrying shortly.",
            )

            raise self.retry(
                exc=error,
                countdown=delay_seconds,
            )

        fail_run(
            run_id=run_id,
            error_message=str(error),
        )

        add_run_event(
            run_id=run_id,
            event_type="failed",
            message="Investigation could not be completed.",
        )
        raise