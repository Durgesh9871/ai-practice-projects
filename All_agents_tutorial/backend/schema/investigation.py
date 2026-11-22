

from pydantic import BaseModel ,Field
from typing import Optional


class InvestigationRequest(BaseModel):
    objective: str = Field(..., description="The investigation objective" , min_length=10, max_length=500)
    thread_id:  Optional[str] = Field(None, description="The thread ID" )



class InvestigationResponse(BaseModel):
    run_id: str
    thread_id: str
    status: str
    final_report: str



class InvestigationRunResponse(BaseModel):
    run_id: str
    thread_id: str
    objective: str
    status: str
    final_report: str | None
    error_message: str | None
    created_at: str
    updated_at: str


class ChatMessageResponse(BaseModel):
    message_id: str
    run_id: str
    role: str
    content: str
    created_at: str