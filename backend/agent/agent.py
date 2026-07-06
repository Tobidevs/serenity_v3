from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from agent.state import AgentState
from agent.nodes import planner_node

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)


    

    graph.add_node("planner", planner_node)

    return graph


graph = build_graph().compile()
