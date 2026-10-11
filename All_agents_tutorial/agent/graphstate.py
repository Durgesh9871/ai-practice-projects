from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class InvestigationGraphState(TypedDict):
    """ Represents the state of the investigation."""
    messages: Annotated[list[BaseMessage], add_messages]
    hypotheses:list[str]
    findings: list[str]
    objective:str
    tool_calls: int
    step_count: int
    is_finished: bool
    final_report: str
