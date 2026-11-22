from dataclasses import dataclass
from typing import Literal


RunStatus = Literal[
    "running",
    "completed",
    "failed",
    "stopped",
    "queued"
]



@dataclass
class InvestigationRun:
    run_id: str
    thread_id: str
    objective: str
    status: RunStatus
    final_report: str = ""
    error_message: str = ""



class InvestigationEventResponse(BaseModel):
    event_id: str
    run_id: str
    event_sequence: int
    event_type: str
    message: str
    created_at: str    