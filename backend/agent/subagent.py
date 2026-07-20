import json
from functools import lru_cache

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, ToolMessage
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

def _current_turn_tool_messages(messages: list) -> list[ToolMessage]:
    """ToolMessages answering the tool calls in the latest model turn.

    Correlating on tool_call_id rather than list position keeps this correct
    when the model issues several tool calls at once, and stops an earlier
    turn's results from being reprocessed on the next loop iteration.
    """
    ai = next(
        (m for m in reversed(messages) if isinstance(m, AIMessage) and m.tool_calls),
        None,
    )
    if ai is None:
        return []

    ids = {tool_call["id"] for tool_call in ai.tool_calls}
    return [
        m for m in messages if isinstance(m, ToolMessage) and m.tool_call_id in ids
    ]
    
def _intercept_search_results(
    message: ToolMessage,
) -> tuple[list[dict], ToolMessage] | None:
    """Split an exa_search result into citation metadata and a model-facing view.

    Returns the records to persist in `search_info` and a replacement
    ToolMessage stripped of favicons. The replacement reuses the original's id
    so `add_messages` overwrites it in place rather than appending a duplicate.

    Returns None when the message carries no usable results — a failed search
    has to reach the model as its original error text, not as an empty result
    set it would read as "no sources exist".
    """
    if message.status == "error":
        return None

    # exa_search returns its records as a JSON string in `content`; anything that
    # doesn't parse into a list is not a search payload we can lift metadata from.
    try:
        records = json.loads(message.content)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(records, list):
        return None
    sources = [
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
        status=message.status,
    )
    return sources, trimmed
    
    
def llm_node(state: SubAgentState) -> dict:
    """Invoke the sub-agent model, intercepting exa_search results on the way in.

    Every search in the current turn has its title/url/favicon lifted into
    `search_info`, and the favicon dropped from what the model sees.
    """
    messages = state["messages"]
    replacements = dict[str, ToolMessage] = {}
    
    for message in _current_turn_tool_messages(messages):
        # Without an id there is no way to overwrite in place, and returning the
        # trimmed copy would append a duplicate instead.
        if message.name != "exa_search" or message.id is None:
            continue
        intercepted = _intercept_search_results(message)
        if intercepted is None:
            continue
        sources, trimmed = intercepted
        sources.extend(sources)
        replacements[message.id] = trimmed
        
    if not replacements:
        return {"messages": [_subagent_model().invoke(messages)]}

    # Non-ToolMessages never match a key, so this swaps only the intercepted ones.
    model_messages = [replacements.get(m.id, m) for m in messages]
    response = _subagent_model().invoke(model_messages)
    
    return {
        "messages": [*replacements.values(), response],
        "sources": sources,
    }
    

def process_search_results(state: SubAgentState) -> dict:
    pass


def is_finished(state: SubAgentState) -> str:
    """Route to reporting once the model has called submit_findings."""
    for message in _current_turn_tool_messages(state["messages"]):
        if message.name == "submit_findings":
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
