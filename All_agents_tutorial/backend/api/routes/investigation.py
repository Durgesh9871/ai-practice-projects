
from fastapi import APIRouter, HTTPException, Depends, status

from backend.schema.investigation import InvestigationRequest, InvestigationResponse

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