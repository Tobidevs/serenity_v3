from typing import Annotated, Literal, TypedDict
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    current_query: str


class PlanStep(BaseModel):
    step_number: str
    step_name: str
    description: str
    
class Plan(BaseModel):
    steps: list[PlanStep]

class PlannerOutput(BaseModel):
    route: Annotated[Literal["continue_to_supervisor", "ask_for_clarification", "bypass_to_generation"]]
    refined_query: Annotated[str] | None
    clarification_request: Annotated[str, Field(default="")] | None
    plan: Annotated[Plan, Field(default_factory=Plan)] | None