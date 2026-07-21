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
    return [m for m in messages if isinstance(m, ToolMessage) and m.tool_call_id in ids]


def _latest_ai_message(messages: list) -> AIMessage | None:
    """The most recent AIMessage, whether or not it carried tool calls.

    Routing keys off this: a turn with no tool calls is the model's implicit
    "I'm done", so we must see the toolless turn itself rather than skipping
    back to an earlier one that did call a tool.
    """
    return next(
        (m for m in reversed(messages) if isinstance(m, AIMessage)),
        None,
    )


MAX_STEPS = 8


def _format_search_results(records: list[dict]) -> str:
    """Render search records as labeled, numbered text for the model to read.

    Plain JSON forces the model to parse escaped strings and match brackets to
    tell one result from another. Labeled fields under a bracketed index make
    the title/url/highlight boundaries unambiguous and let the model cite a
    source by its number. `highlights` is a list, so each entry becomes its own
    bullet; missing fields degrade to a placeholder rather than "None".
    """
    blocks = []
    for i, record in enumerate(records, start=1):
        title = record.get("title") or "(no title)"
        url = record.get("url") or "(no url)"
        highlights = record.get("highlights") or []

        lines = [f"[{i}] TITLE: {title}", f"    URL: {url}"]
        if highlights:
            lines.append("    HIGHLIGHTS:")
            lines.extend(f"      - {h}" for h in highlights)
        else:
            lines.append("    HIGHLIGHTS: (none)")
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


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
        content=_format_search_results(model_view),
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
    replacements: dict[str, ToolMessage] = {}
    sources: list[dict] = []

    for message in _current_turn_tool_messages(messages):
        # Without an id there is no way to overwrite in place, and returning the
        # trimmed copy would append a duplicate instead.
        if message.name != "exa_search" or message.id is None:
            continue
        intercepted = _intercept_search_results(message)
        if intercepted is None:
            continue
        record_sources, trimmed = intercepted
        sources.extend(record_sources)
        replacements[message.id] = trimmed

    if not replacements:
        return {"messages": [_subagent_model().invoke(messages)], "steps": 1}

    # Non-ToolMessages never match a key, so this swaps only the intercepted ones.
    model_messages = [replacements.get(m.id, m) for m in messages]
    response = _subagent_model().invoke(model_messages)

    return {
        "messages": [*replacements.values(), response],
        "sources": sources,
        "steps": 1,
    }


def process_search_results(state: SubAgentState) -> dict:
    """Lift the findings text out of the submit_findings call into state.

    Both finish paths land here, so the call is often absent: an implicit
    finish or the MAX_STEPS backstop arrives with no submit_findings at all.
    That is a normal exit, not an error, so it writes nothing.
    """
    last_ai = _latest_ai_message(state["messages"])
    if last_ai is None or not last_ai.tool_calls:
        return {}

    for call in last_ai.tool_calls:
        if call["name"] != "submit_findings":
            continue
        findings = call.get("args", {}).get("findings")
        if findings:
            return {"findings": [findings]}
    return {}


def route_after_llm(state: SubAgentState) -> str:
    """Decide where the loop goes after the model speaks.

    Runs after llm (not after tool) so a turn with no tool calls terminates
    instead of looping: ToolNode would no-op on it and the old post-tool check
    would route back to llm forever. Order matters — implicit finish is checked
    before submit_findings so a toolless turn can never fall through to a tool
    dispatch, and the step backstop caps a model that keeps searching.
    """
    ai = _latest_ai_message(state["messages"])
    if ai is None or not ai.tool_calls:
        return "tool_results"
    if any(call["name"] == "submit_findings" for call in ai.tool_calls):
        return "process_search_results"
    if state.get("steps", 0) >= MAX_STEPS:
        return "tool_results"
    return "tool"


subgraph = StateGraph(SubAgentState)

subgraph.add_node("llm", llm_node)
subgraph.add_node("tool", ToolNode([exa_search, think, submit_findings]))
subgraph.add_node("process_search_results", process_search_results)

subgraph.add_edge(START, "llm")
subgraph.add_conditional_edges(
    "llm",
    route_after_llm,
    {
        "tool": "tool",
        "process_search_results": "process_search_results",
        "tool_results": "process_search_results",
    },
)
subgraph.add_edge("tool", "llm")
subgraph.add_edge("process_search_results", END)
