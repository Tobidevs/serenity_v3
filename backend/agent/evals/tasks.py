from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from agent.prompts import PLANNER_NODE_SYSTEM_PROMPT, SUBAGENT_SYSTEM_PROMPT
from ..nodes import _planner_model
from ..state import PlannerOutput


def planner_eval_task(input):
    result: PlannerOutput = _planner_model().invoke(
        [SystemMessage(content=PLANNER_NODE_SYSTEM_PROMPT), *input["messages"]]
    )

    return {
        "route": result.route,
        "refined_query": result.refined_query or "",
        "clarification_request": result.clarification_request or "",
        "denominational_scope": result.denominational_scope,
        "plan": result.plan.model_dump() if result.plan else {"steps": []},
    }


def _extract_search_trace(messages: list, search_trace: list[dict]) -> tuple[str, int]:
    """Pair each exa_search call's arguments with the results it returned.

    The sub-agent's queries (main_query/guiding_query/domain_scope) live only in
    the AIMessage tool_calls. The results do NOT live in the messages any more:
    once a report covers a result set, the loop overwrites that ToolMessage with
    a short index and the excerpts are gone. Grading against the messages would
    show the judge "[results consumed into a partial report]" for every search
    but the last, and it would score the report as uncited against evidence it
    could no longer see.

    `search_trace` is the snapshot taken before that overwrite, keyed by the
    call it answers. The messages are still the fallback: a search that FAILED
    is never rendered and so never reaches the trace, and its error text is
    exactly what the judge needs to see to forgive the empty yield.
    """
    results_by_id = {
        m.tool_call_id: m.content
        for m in messages
        if isinstance(m, ToolMessage) and m.name == "exa_search"
    }
    results_by_id.update(
        {entry["tool_call_id"]: entry["results"] for entry in search_trace}
    )

    blocks: list[str] = []
    n = 0
    for m in messages:
        if not isinstance(m, AIMessage) or not m.tool_calls:
            continue
        for call in m.tool_calls:
            if call["name"] != "exa_search":
                continue
            n += 1
            args = call.get("args", {})
            result = results_by_id.get(call["id"], "(no results returned)")
            blocks.append(
                f"SEARCH {n}\n"
                f"  main_query: {args.get('main_query')}\n"
                f"  guiding_query: {args.get('guiding_query')}\n"
                f"  domain_scope: {args.get('domain_scope')}\n"
                f"  RESULTS:\n{result}"
            )

    return "\n\n".join(blocks), n


def research_eval_task(input):
    """Run the research sub-agent on a topic and shape its trace for the judge.

    Invokes the real search_subagent graph (live Anthropic + Exa calls), then
    surfaces what the three fidelity dimensions need: the search trace (strategy
    + citation evidence), the submitted report, the published sources, and any
    llm_error that cut the run short.
    """
    # Imported lazily: agent.tools constructs its Exa client at import time, so
    # keeping this out of the module top lets tasks.py (and the planner eval that
    # shares it) import without EXA_API_KEY. The key is only needed to actually
    # run research, which needs Exa anyway.
    from ..subagent import build_user_message, search_subagent

    result = search_subagent.invoke(
        {
            "messages": [
                SystemMessage(content=SUBAGENT_SYSTEM_PROMPT),
                HumanMessage(content=build_user_message(input["topic"])),
            ],
            "sources": [],
            "steps": 0,
            "findings": [],
            "final_sources": [],
            "partial_reports": [],
            "search_trace": [],
        }
    )

    messages = result.get("messages", [])
    search_trace, num_searches = _extract_search_trace(
        messages, result.get("search_trace", [])
    )

    return {
        "topic": input["topic"],
        "findings": "\n\n".join(result.get("findings", [])),
        "num_searches": num_searches,
        "search_trace": search_trace,
        "final_sources": result.get("final_sources", []),
        "steps": result.get("steps", 0),
        "llm_error": result.get("llm_error"),
        "findings_source": result.get("findings_source") or "none",
        # Not shown to the judge, which grades the finished report. Recorded so
        # a bad score can be traced to the turn that lost the information —
        # whether the distillation dropped it or the final merge did.
        "partial_reports": result.get("partial_reports", []),
    }
