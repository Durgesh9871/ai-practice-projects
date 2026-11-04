from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from operator import add

class Observation_Dict(TypedDict):
    tool_name: str
    tool_call_id: str
    arguments: dict
    content: str


class InvestigationGraphState(TypedDict):
    """Represents the state of the investigation."""

    messages: Annotated[list[BaseMessage], add_messages]
    hypotheses: list[str]
    findings: list[str]
    objective: str
    tool_calls: int
    step_count: int
    is_finished: bool
    final_report: str
    tool_observation: Annotated[list[Observation_Dict], add]
