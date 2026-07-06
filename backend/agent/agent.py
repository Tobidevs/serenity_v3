from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from agent.nodes import (
    planner_node,
    report_generation,
    request_clarification_node,
    route_from_planner,
    supervisor_node,
)
from agent.state import AgentState


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("clarification", request_clarification_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("report_generation", report_generation)

    graph.add_edge(START, "planner")
    graph.add_conditional_edges(
        "planner",
        route_from_planner,
        {
            "continue_to_supervisor": "supervisor",
            "ask_for_clarification": "clarification",
            "bypass_to_generation": "report_generation",
        },
    )
    # After the user answers a clarification, re-plan with the new context.
    graph.add_edge("clarification", "planner")
    graph.add_edge("supervisor", "report_generation")
    graph.add_edge("report_generation", END)

    return graph


# MemorySaver is required for interrupt()/resume to work. It is in-memory only;
# swap for a persistent checkpointer (e.g. Postgres) for production.
graph = build_graph().compile(checkpointer=MemorySaver())
