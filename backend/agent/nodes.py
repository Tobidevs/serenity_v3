from functools import lru_cache

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage
from langgraph.types import interrupt

from agent.prompts import PLANNER_NODE_SYSTEM_PROMPT
from agent.state import AgentState, PlannerOutput, Route

from dotenv import load_dotenv
load_dotenv()

@lru_cache(maxsize=1)
def _planner_model():
    """Lazily build the structured planner model.

    Cached so we only construct the client once, and lazy so importing this
    module doesn't require ANTHROPIC_API_KEY (e.g. during tests/graph build).
    """
    model = init_chat_model("claude-haiku-4-5-20251001", model_provider="anthropic", temperature=0)
    return model.with_structured_output(PlannerOutput)


def planner_node(state: AgentState) -> dict:
    """Run the planner LLM and write its decision into state.

    The planner is fed the entire message history and returns a structured
    PlannerOutput. Routing itself is handled by `route_from_planner`.
    """
    result: PlannerOutput = _planner_model().invoke(
        [SystemMessage(content=PLANNER_NODE_SYSTEM_PROMPT), *state["messages"]]
    )

    return {
        "route": result.route,
        "refined_query": result.refined_query or "",
        "clarification_request": result.clarification_request or "",
        "plan": result.plan,
        "denominational_scope": result.denominational_scope,
    }


def route_from_planner(state: AgentState) -> Route:
    """Conditional edge: pick the next node based on the planner's route."""
    return state["route"]


def request_clarification_node(state: AgentState) -> dict:
    """Interrupt the graph and surface the planner's clarification question.

    Execution pauses here; the value passed to `interrupt` is what the caller
    sees. When resumed with `Command(resume=<answer>)`, that answer is appended
    to the conversation and the graph loops back to the planner to re-plan.
    """
    answer = interrupt(state["clarification_request"])
    return {"messages": [{"role": "user", "content": answer}]}


def supervisor_node(state: AgentState) -> dict:
    pass


def report_generation(state: AgentState) -> dict:
    pass
