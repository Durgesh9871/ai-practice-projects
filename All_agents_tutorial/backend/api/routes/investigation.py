
from fastapi import APIRouter, HTTPException, Depends, status


from agent.persistence.repository import (
    get_run,
    get_run_messages,
    get_thread_runs,
)
from backend.schema.investigation import (
    ChatMessageResponse,
    InvestigationRequest,
    InvestigationResponse,
    InvestigationRunResponse,
)

from agent.services.investigation_service import (
    execute_investigation,
)
import duckdb
from backend.dependencies import get_analytics_connection





router = APIRouter(prefix="/investigation", tags=["investigation"])


@router.post("", response_model=InvestigationResponse, status_code=status.HTTP_201_CREATED)

def create_investigation(payload: InvestigationRequest, db: duckdb.DuckDBPyConnection = Depends(get_analytics_connection)):
    try:
        result = execute_investigation(objective=payload.objective, analytics_connection=db , thread_id=payload.thread_id)
        return InvestigationResponse(
            run_id=result["run_id"],
            thread_id=result["thread_id"],
            status=result["status"],
            final_report=result.get("final_report", ""),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")



@router.get("/runs/{run_id}", response_model=InvestigationRunResponse , status_code=status.HTTP_200_OK)        
def get_investigation_run(run_id: str) -> InvestigationRunResponse:
    try:
        run = get_run(run_id)
        if not run:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation run not found")
        return InvestigationRunResponse(**run)
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
        


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
