from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from operator import add

class Observation_Dict(TypedDict):
    tool_name: str
    tool_call_id: str
    arguments: dict
    content: str


class Hypothesis(TypedDict):
    statement: str
    status: str  # open, supported, rejected


class Finding(TypedDict):
    statement: str
    evidence_ids: list[str]
    confidence: float

class SQLAttempt(TypedDict):
    query: str
    normalized_query: str
    tool_call_id: str
    success: bool
    error: str



class InvestigationGraphState(TypedDict):
    """Represents the state of the investigation."""

    messages: Annotated[list[BaseMessage], add_messages]
    hypotheses: Annotated[list[Hypothesis], add]
    findings: Annotated[list[Finding], add]
    objective: str
    tool_calls: int
    step_count: int
    is_finished: bool
    final_report: str
    tool_observation: Annotated[list[Observation_Dict], add]
    completion_valid: bool
    completion_feedback: str
    completion_attempts: int
    sql_attempts: Annotated[list[SQLAttempt], add]
    sql_error_count: int
    last_sql_error: str
