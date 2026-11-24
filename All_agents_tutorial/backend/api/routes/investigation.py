
from fastapi import APIRouter, HTTPException, Depends, status,Request

import asyncio
import json
from fastapi.responses import StreamingResponse

from agent.persistence.repository import (
    get_run,
    get_run_messages,
    get_thread_runs,
    get_run_events,
)
from backend.schema.investigation import (
    ChatMessageResponse,
    InvestigationRequest,
    InvestigationResponse,
    InvestigationRunResponse,
    InvestigationQueuedResponse,
    InvestigationEventResponse,
)

import logging

from agent.persistence.repository import fail_run
from agent.services.investigation_service import (
    create_queued_investigation,
)
from backend.tasks.investigation_tasks import (
    execute_investigation_task,
)


logger = logging.getLogger(__name__)





router = APIRouter(prefix="/investigation", tags=["investigation"])


@router.post(
    "",
    response_model=InvestigationQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_investigation(payload: InvestigationRequest):
    investigation = create_queued_investigation(
        objective=payload.objective,
        thread_id=payload.thread_id,
    )

    try:
        execute_investigation_task.delay(
            run_id=investigation["run_id"],
            thread_id=investigation["thread_id"],
            objective=investigation["objective"],
        )
    except Exception as error:
        fail_run(
            run_id=investigation["run_id"],
            error_message=str(error),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Investigation could not be queued.",
        )

    return InvestigationQueuedResponse(
        run_id=investigation["run_id"],
        thread_id=investigation["thread_id"],
        status=investigation["status"],
    )



@router.get(
    "/runs/{run_id}/events",
    response_model=list[InvestigationEventResponse],
)
def read_run_events(run_id: str):
    run = get_run(run_id)

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation run not found.",
        )

    return get_run_events(run_id)
    
    

@router.get("/runs/{run_id}", response_model=InvestigationRunResponse , status_code=status.HTTP_200_OK)        
def get_investigation_run(run_id: str):
    try:
        run = get_run(run_id)
        if not run:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation run not found")
        return InvestigationRunResponse(**run)
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    # except Exception:
    #     raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
        


@router.get(
    "/threads/{thread_id}/runs",
    response_model=list[InvestigationRunResponse],
)
def read_thread_runs(thread_id: str):
    return get_thread_runs(thread_id)


@router.get(
    "/runs/{run_id}/messages",
    response_model=list[ChatMessageResponse],
)
def read_run_messages(run_id: str):
    run = get_run(run_id)

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation run not found.",
        )

    return get_run_messages(run_id)



@router.get("/runs/{run_id}/stream")
async def stream_run_events(
    run_id: str,
    request: Request,
):
    run = await asyncio.to_thread(get_run, run_id)

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation run not found.",
        )

    async def event_generator():
        last_event_sequence = 0

        while True:
            events = await asyncio.to_thread(
                get_run_events,
                run_id,
            )

            new_events = [
                event
                for event in events
                if event["event_sequence"] > last_event_sequence
            ]

            for event in new_events:
                last_event_sequence = event["event_sequence"]

                yield (
                    f"id: {event['event_sequence']}\n"
                    f"event: {event['event_type']}\n"
                    f"data: {json.dumps(event)}\n\n"
                )

                if event["event_type"] in {"completed", "failed"}:
                    return

            if await request.is_disconnected():
                return

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )