

from pydantic import BaseModel ,Field
from typing import Optional


class InvestigationRequest(BaseModel):
    objective: str = Field(..., description="The investigation objective" , min_length=10, max_length=500)
    thread_id:  Optional[str] = Field(None, description="The thread ID" , min_length=1)



class InvestigationResponse(BaseModel):
    run_id: str
    thread_id: str
    status: str
    final_report: str