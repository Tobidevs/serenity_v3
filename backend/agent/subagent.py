import json
from functools import lru_cache

from langchain.chat_models import init_chat_model
from langchain_core.messages import ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from .state import SubAgentState
from .tools import exa_search, submit_findings, think


@lru_cache(maxsize=1)
def _subagent_model():
    """Lazily build the structured planner model.

    Cached so we only construct the client once, and lazy so importing this
    module doesn't require ANTHROPIC_API_KEY (e.g. during tests/graph build).
    """
    model = init_chat_model(
        "claude-haiku-4-5-20251001", model_provider="anthropic", temperature=0
    )
    return model.bind_tools([exa_search, think, submit_findings])


def _intercept_search_results(message: ToolMessage) -> tuple[list[dict], ToolMessage]:
    """Split an exa_search result into citation metadata and a model-facing view.

    Returns the records to persist in `search_info` and a replacement
    ToolMessage stripped of favicons. The replacement reuses the original's id
    so `add_messages` overwrites it in place rather than appending a duplicate.
    """
    records = message.artifact or []

    search_info = [
        {"title": r.get("title"), "url": r.get("url"), "favicon": r.get("favicon")}
        for r in records
    ]
    model_view = [
        {
            "title": r.get("title"),
            "url": r.get("url"),
            "highlights": r.get("highlights"),
        }
        for r in records
    ]

    trimmed = ToolMessage(
        content=json.dumps(model_view),
        tool_call_id=message.tool_call_id,
        name=message.name,
        id=message.id,
    )
    return search_info, trimmed


def llm_node(state: SubAgentState) -> dict:
    """Invoke the sub-agent model, intercepting exa_search results on the way in.

    When the previous step was a search, its title/url/favicon are lifted into
    `search_info` and the favicon is dropped from what the model sees.
    """
    messages = state["messages"]
    last = messages[-1] if messages else None

    if isinstance(last, ToolMessage) and last.name == "exa_search":
        search_info, trimmed = _intercept_search_results(last)
        messages = [*messages[:-1], trimmed]
        response = _subagent_model().invoke(messages)
        return {"messages": [trimmed, response], "search_info": search_info}

    return {"messages": [_subagent_model().invoke(messages)]}


def process_search_results(SubAgentState):
    pass


def is_finished(SubAgentState):
    last_message = SubAgentState["messages"][-1]

    if last_message.type == "tool":
        if last_message.name == "submit_findings":
            return "process_search_results"
    return "llm"


subgraph = StateGraph(SubAgentState)

subgraph.add_node("llm", llm_node)
subgraph.add_node("tool", ToolNode([exa_search, think, submit_findings]))
subgraph.add_node("process_search_results", process_search_results)

subgraph.add_edge(START, "llm")
subgraph.add_edge("llm", "tool")
subgraph.add_conditional_edges(
    "tool",
    is_finished,
    {
        "llm": "llm",
        "process_search_results": "process_search_results",
    },
)
subgraph.add_edge("process_search_results", END)
