from dataclasses import dataclass
from typing import Literal


RunStatus = Literal[
    "running",
    "completed",
    "failed",
    "stopped",
]


@dataclass
class InvestigationRun:
    run_id: str
    thread_id: str
    objective: str
    status: RunStatus
    final_report: str = ""
    error_message: str = ""