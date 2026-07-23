from functools import lru_cache

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage
from langgraph.types import interrupt

from agent.prompts import PLANNER_NODE_SYSTEM_PROMPT
from agent.resilience import LLMCallFailed, safe_invoke, with_llm_retry
from agent.state import AgentState, Plan, PlannerOutput, Route

from dotenv import load_dotenv
load_dotenv()

# Shown to the user when the planner can't be reached at all. The graph routes
# to the clarification node to deliver it, which pauses on interrupt() and
# re-plans with whatever the user says next — so a transient outage costs the
# user a rephrase rather than the whole thread.
PLANNER_FAILURE_MESSAGE = (
    "Sorry — I had trouble processing that just now. "
    "Could you send your question again?"
)


@lru_cache(maxsize=1)
def _planner_model():
    """Lazily build the structured planner model.

    Cached so we only construct the client once, and lazy so importing this
    module doesn't require ANTHROPIC_API_KEY (e.g. during tests/graph build).
    """
    model = init_chat_model("claude-haiku-4-5-20251001", model_provider="anthropic", temperature=0)
    return with_llm_retry(model.with_structured_output(PlannerOutput))


def planner_node(state: AgentState) -> dict:
    """Run the planner LLM and write its decision into state.

    The planner is fed the entire message history and returns a structured
    PlannerOutput. Routing itself is handled by `route_from_planner`.

    The planner is the graph's entry node, so an unhandled failure here loses
    the run. Instead we degrade to a clarification: the user gets a plain
    apology and a chance to retry, and the thread stays alive.
    """
    try:
        result: PlannerOutput = safe_invoke(
            _planner_model,
            [SystemMessage(content=PLANNER_NODE_SYSTEM_PROMPT), *state["messages"]],
            label="planner",
        )
    except LLMCallFailed:
        # Clear the planning fields rather than leaving a previous turn's values
        # in place: this run produced no plan, and a stale one read as current
        # would send the supervisor off researching the wrong question.
        return {
            "route": "ask_for_clarification",
            "refined_query": "",
            "clarification_request": PLANNER_FAILURE_MESSAGE,
            "plan": Plan(),
        }

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
