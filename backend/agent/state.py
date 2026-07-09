from typing import Annotated, Literal, Optional, TypedDict

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

Route = Literal["continue_to_supervisor", "ask_for_clarification", "bypass_to_generation"]
Denominational_Scope = Literal[
    "neutral_baseline",
    "neutral_with_denominational_support",
    "denominational_support",
    "comparative",
]
Tool = Literal["subagent", "bible_api", "greek_hebrew_tool", ]

class PlanStep(BaseModel):
    step_number: str
    tool: Tool
    step_name: str
    description: str


class Plan(BaseModel):
    steps: list[PlanStep] = Field(default_factory=list)


class PlannerOutput(BaseModel):
    route: Route
    refined_query: Optional[str] = None
    clarification_request: Optional[str] = Field(default="")
    plan: Optional[Plan] = Field(default_factory=Plan)
    denominational_scope: Denominational_Scope


class AgentState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    current_query: str
    # Planner outputs, written by planner_node and read by downstream nodes.
    route: Route
    refined_query: str
    clarification_request: str
    plan: Plan
    denominational_scope: Denominational_Scope
