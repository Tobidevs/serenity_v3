import json
import re
from functools import lru_cache

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from .resilience import LLMCallFailed, safe_invoke, with_llm_retry
from .state import SubAgentState
from .tools import exa_search, record_findings


@lru_cache(maxsize=1)
def _subagent_model():
    """Lazily build the tool-calling sub-agent model.

    Cached so we only construct the client once, and lazy so importing this
    module doesn't require OPENAI_API_KEY (e.g. during tests/graph build).
    """
    model = init_chat_model(
        "gpt-5.4-mini",
        model_provider="openai",
        temperature=0,

    )
    return with_llm_retry(model.bind_tools([exa_search, record_findings]))

def build_user_message(topic: str) -> str:
    """Frame the Supervisor's research topic as the sub-agent's assignment.

    The sub-agent is seeded with SUBAGENT_SYSTEM_PROMPT followed by this string
    as its user turn; the prompt treats the topic as "your assignment," so a
    light label is all the framing it needs.
    """
    return f"Research topic: {topic}"

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


def _report_calls(ai: AIMessage) -> list[dict]:
    """Every record_findings call in a turn, in the order the model made them."""
    return [call for call in ai.tool_calls if call["name"] == "record_findings"]


def _report_call(ai: AIMessage) -> dict | None:
    """The record_findings call that decides what happens to the run.

    Normally there is at most one. When a turn carries several — parallel tool
    calls make that possible — the one that ends the run wins. Taking the first
    instead would let a stray partial keep the loop going while the full
    report's text, the only copy of it, went nowhere.
    """
    calls = _report_calls(ai)
    if not calls:
        return None
    return next(
        (call for call in calls if call.get("args", {}).get("report_type") == "full"),
        calls[0],
    )


def _search_count(messages: list) -> int:
    """exa_search calls issued so far, including the turn being routed.

    Counted from the message history rather than tracked in state so the ceiling
    cannot drift out of sync with what was actually dispatched.
    """
    return sum(
        1
        for m in messages
        if isinstance(m, AIMessage)
        for call in m.tool_calls
        if call["name"] == "exa_search"
    )


# Turns are fused — one model turn reports on the last search and issues the
# next one — so the loop needs only about MAX_SEARCHES + 1 turns and this stays
# a backstop rather than the binding limit.
MAX_STEPS = 8
# The ceiling SUBAGENT_SYSTEM_PROMPT already tells the sub-agent to respect.
# MAX_STEPS counts llm turns, so it can't enforce this one: a single turn may
# carry several searches.
MAX_SEARCHES = 5

# Marks a result set the model has already distilled. Doubles as the guard that
# keeps a stub from being rewritten on a later turn.
#
# Stubbing costs cache: the prefix diverges from that message onwards on the
# turn it happens, which is the price of the trade and is paid once per result
# set. The guard is what keeps it to once — re-stubbing an already-stubbed
# message would move the divergence point back to it on every later turn, and
# the run would stop reading cache almost entirely.
STUB_MARKER = "[results consumed into a partial report]"

# Pulls the citation number and title back out of already-rendered results, so
# a stub can be built from the message alone rather than stashing the parsed
# records somewhere on the side.
_RENDERED_HEAD = re.compile(r"^\[(\d+|-)\] TITLE: (.*)$", re.MULTILINE)

# Citation markers in a finished report, used to list only what it actually cites.
_CITATION = re.compile(r"\[(\d+)\]")


def _source_ledger(sources: list[dict]) -> dict[str, int]:
    """Map each distinct source url to the number the model cites it by.

    Numbers are handed out in order of first appearance and never reused, so a
    number means the same source on every turn and in the final SOURCES block.
    Both the model-facing labels and the published source list derive from this
    one function — deriving them separately is exactly how [3] ends up naming
    two different sources.

    A source with no url is skipped: it can be neither deduped nor cited, which
    is the rule `process_search_results` already applies to `final_sources`.
    """
    ledger: dict[str, int] = {}
    for source in sources:
        url = source.get("url")
        if not url or url in ledger:
            continue
        ledger[url] = len(ledger) + 1
    return ledger


def _host(url: str | None) -> str:
    """The bare host of a url, for showing provenance without showing the url."""
    if not url:
        return "(no source)"
    stripped = re.sub(r"^https?://(www\.)?", "", url)
    return stripped.split("/", 1)[0] or "(no source)"


def _format_search_results(records: list[dict], ledger: dict[str, int]) -> str:
    """Render search records as labeled, numbered text for the model to read.

    Plain JSON forces the model to parse escaped strings and match brackets to
    tell one result from another. Labeled fields under a bracketed index make
    the title/highlight boundaries unambiguous and let the model cite a source
    by its number. `highlights` is a list, so each entry becomes its own bullet;
    missing fields degrade to a placeholder rather than "None".

    Numbers come from the ledger rather than this result set's position, so the
    third hit of the second search is not another `[3]`.

    The full url is deliberately withheld. The model cites numbers and the
    harness renders the urls, so a url it never sees is a url it cannot get
    wrong. The host is kept because the prompt asks the model to note a
    source's own stance, and that is most of what the host tells it. A record
    with no url is marked `[-]`: uncitable, and the prompt says to leave it be.
    """
    blocks = []
    for record in records:
        title = record.get("title") or "(no title)"
        url = record.get("url")
        number = ledger.get(url) if url else None
        highlights = record.get("highlights") or []

        label = str(number) if number is not None else "-"
        lines = [f"[{label}] TITLE: {title}", f"    SOURCE: {_host(url)}"]
        if highlights:
            lines.append("    HIGHLIGHTS:")
            lines.extend(f"      - {h}" for h in highlights)
        else:
            lines.append("    HIGHLIGHTS: (none)")
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def _parse_records(message: ToolMessage) -> list[dict] | None:
    """The search records carried by an exa_search ToolMessage, if it has any.

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
    return records


def _replace(message: ToolMessage, content: str) -> ToolMessage:
    """A copy of a ToolMessage carrying new content.

    Reuses the original's id so `add_messages` overwrites it in place rather
    than appending a duplicate.
    """
    return ToolMessage(
        content=content,
        tool_call_id=message.tool_call_id,
        name=message.name,
        id=message.id,
        status=message.status,
    )


def _reported_search_messages(messages: list) -> list[ToolMessage]:
    """exa_search results the model has already distilled into a report.

    A result set qualifies once a record_findings call appears after it: the
    model has read those results and written down what mattered, so the raw
    excerpts are dead weight competing for attention with the report itself.

    Anything newer than the last report is left alone. That is the invariant
    the whole design rests on — results the model has not yet reported on are
    never dropped, so a turn that issues two searches before reporting keeps
    both result sets in full until a report covers them.
    """
    last_report = -1
    for i, message in enumerate(messages):
        if isinstance(message, AIMessage) and _report_call(message) is not None:
            last_report = i
    if last_report < 0:
        return []

    return [
        m
        for m in messages[:last_report]
        if isinstance(m, ToolMessage) and m.name == "exa_search" and m.id is not None
    ]


def _stub_search_message(message: ToolMessage) -> ToolMessage | None:
    """Swap a reported-on result set for a one-line-per-result index.

    Keeps every result's citation number and title so the model still knows
    what it has seen — and can go back for it if a later search shows it
    mattered after all — without carrying excerpts it has already distilled.
    The queries stay visible too: they live in the AIMessage's tool_calls,
    which is never touched.

    Returns None when there is nothing to do — an already-stubbed message, an
    error the model still needs to read, or content that was never rendered
    results in the first place.
    """
    content = message.content
    if not isinstance(content, str) or content.startswith(STUB_MARKER):
        return None
    entries = _RENDERED_HEAD.findall(content)
    if not entries:
        return None

    lines = [STUB_MARKER, "seen:"]
    lines.extend(f"  [{number}] {title}" for number, title in entries)
    return _replace(message, "\n".join(lines))


def llm_node(state: SubAgentState) -> dict:
    """Invoke the sub-agent model, rewriting search results on the way in.

    Two rewrites happen here, both in place:

    1. The turn's fresh results are stripped of favicons, numbered from the
       ledger, and rendered for the model. Their metadata is lifted into
       `sources`, and a copy of what the model was shown into `search_trace`.
    2. Results the model has already reported on collapse to an index line each.

    A call that fails for good writes `llm_error` instead of a model turn, which
    `route_after_llm` reads as "stop here and publish what we have".
    """
    messages = state["messages"]
    replacements: dict[str, ToolMessage] = {}
    sources: list[dict] = []
    trace: list[str] = []

    # Parsed first, rendered second: the ledger has to know about every url in
    # this turn before any of them can be given a number.
    fresh: list[tuple[ToolMessage, list[dict]]] = []
    for message in _current_turn_tool_messages(messages):
        # Without an id there is no way to overwrite in place, and returning the
        # trimmed copy would append a duplicate instead.
        if message.name != "exa_search" or message.id is None:
            continue
        records = _parse_records(message)
        if records is None:
            continue
        fresh.append((message, records))
        sources.extend(
            {
                "title": r.get("title"),
                "url": r.get("url"),
                "favicon": r.get("favicon"),
            }
            for r in records
        )

    ledger = _source_ledger([*state.get("sources", []), *sources])
    for message, records in fresh:
        rendered = _format_search_results(records, ledger)
        replacements[message.id] = _replace(message, rendered)
        trace.append(rendered)

    for message in _reported_search_messages(messages):
        # Anything rendered above belongs to this turn, so it is newer than the
        # last report and _reported_search_messages will not have returned it.
        stubbed = _stub_search_message(message)
        if stubbed is not None:
            replacements[message.id] = stubbed

    model_messages = messages
    if replacements:
        # Non-ToolMessages never match a key, so this swaps only the rewritten ones.
        model_messages = [replacements.get(m.id, m) for m in messages]

    try:
        response = safe_invoke(_subagent_model, model_messages, label="sub-agent")
    except LLMCallFailed as exc:
        # The rewrites above already happened, so their sources and messages are
        # published even though the call that would have consumed them failed.
        # `steps` is left alone: no model turn was spent.
        return {
            "messages": [*replacements.values()],
            "sources": sources,
            "search_trace": trace,
            "llm_error": str(exc),
        }

    update: dict = {
        "messages": [*replacements.values(), response],
        "sources": sources,
        "search_trace": trace,
        "steps": 1,
    }

    # Banked as it is written. The raw results behind an early report are gone
    # by the time the loop ends, so a report that only ever lived in `messages`
    # would be unrecoverable on every exit path that skips the full report.
    # Every call is banked, not just the one routing acts on, so a turn that
    # wrote two reports loses neither.
    banked = [
        findings
        for call in _report_calls(response)
        if (findings := call.get("args", {}).get("findings"))
    ]
    if banked:
        update["partial_reports"] = banked

    return update


def _render_sources(report: str, sources: list[dict]) -> str:
    """The SOURCES block for a finished report, rendered from the ledger.

    The model cites numbers and never sees a full url, so it cannot invent one.
    Writing this block here rather than asking the model for it is what makes
    that hold end to end.

    Only numbers the report actually cites are listed, matching the prompt's
    rule that a search hit that was never cited gets no entry. A number the
    report cites that was never issued is dropped rather than rendered as an
    unknown source — there is no url to print for it, and printing the gap into
    the final report helps no one.
    """
    ledger = _source_ledger(sources)
    by_number = {number: url for url, number in ledger.items()}

    titles: dict[str, str] = {}
    for source in sources:
        url = source.get("url")
        if url and url not in titles:
            titles[url] = source.get("title") or "(no title)"

    lines = []
    for number in sorted({int(n) for n in _CITATION.findall(report)}):
        url = by_number.get(number)
        if url is None:
            continue
        lines.append(f"[{number}] {url} — {titles.get(url, '(no title)')}")

    if not lines:
        return ""
    return "SOURCES\n" + "\n".join(lines)


def process_search_results(state: SubAgentState) -> dict:
    """Publish the loop's output: the findings text and a citable source list.

    `sources` collects one entry per search hit and its reducer appends, so the
    same url recurs whenever two searches surface it and the list cannot be
    cleaned in place. The deduped view is written to `final_sources`, leaving
    the raw list intact as a record of what every search returned.

    Every finish path lands here, and most arrive without a full report — an
    implicit finish, the MAX_STEPS backstop, the search ceiling, or an
    `llm_error` exit. Those fall back to the partial reports banked along the
    way, so a run that is cut short still returns the research it did rather
    than nothing at all. `llm_error` is what distinguishes a failed run from
    one that genuinely found nothing.
    """
    seen: set[str] = set()
    unique: list[dict] = []
    for source in state.get("sources", []):
        url = source.get("url")
        # A source with no url can be neither deduped nor cited.
        if not url or url in seen:
            continue
        seen.add(url)
        unique.append(source)

    result: dict = {"final_sources": unique}

    report = None
    last_ai = _latest_ai_message(state["messages"])
    if last_ai is not None and last_ai.tool_calls:
        call = _report_call(last_ai)
        if call is not None and call.get("args", {}).get("report_type") == "full":
            report = call.get("args", {}).get("findings")

    if not report:
        # A full report's own text is banked in partial_reports too, so this
        # only ever runs when there was no full report to prefer.
        partials = [p for p in state.get("partial_reports", []) if p and p.strip()]
        report = "\n\n".join(partials) if partials else None

    if not report:
        return result

    sources_block = _render_sources(report, state.get("sources", []))
    result["findings"] = [f"{report}\n\n{sources_block}" if sources_block else report]
    return result


def route_after_llm(state: SubAgentState) -> str:
    """Decide where the loop goes after the model speaks.

    Runs after llm (not after tool) so a turn with no tool calls terminates
    instead of looping: ToolNode would no-op on it and the old post-tool check
    would route back to llm forever. Order matters — implicit finish is checked
    before the report so a toolless turn can never fall through to a tool
    dispatch, and the search ceiling and step backstop cap a model that keeps
    searching.
    """
    # Checked first, and explicitly: a failed call appends no message, so the
    # latest AIMessage is still the previous turn's — tool calls included, and
    # already answered. Falling through would re-dispatch those same calls and
    # spin the loop until MAX_STEPS.
    if state.get("llm_error"):
        return "tool_results"

    ai = _latest_ai_message(state["messages"])
    if ai is None or not ai.tool_calls:
        return "tool_results"

    report = _report_call(ai)
    if report is not None:
        # Anything other than an explicit "full" counts as a partial, so a
        # malformed argument keeps the loop running under its caps rather than
        # ending the run on a report the model did not mean to finish.
        if report.get("args", {}).get("report_type") == "full":
            return "process_search_results"
        # A partial with no search beside it says there is more to do while
        # doing nothing about it. The next turn could only repeat itself, so
        # publish what has been banked instead of spending the budget on it.
        if not any(call["name"] == "exa_search" for call in ai.tool_calls):
            return "tool_results"

    # Counts the pending turn too, so this blocks the request that would exceed
    # the ceiling rather than the one that reaches it: 5 searches run, a 6th ends
    # the loop and publishes what was gathered.
    if _search_count(state["messages"]) > MAX_SEARCHES:
        return "tool_results"
    if state.get("steps", 0) >= MAX_STEPS:
        return "tool_results"
    return "tool"


subgraph = StateGraph(SubAgentState)

subgraph.add_node("llm", llm_node)
subgraph.add_node("tool", ToolNode([exa_search, record_findings]))
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

search_subagent = subgraph.compile()
