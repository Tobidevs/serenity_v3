"""`route_after_llm` — the loop's exit conditions.

Routing runs after the LLM turn rather than after the tool node, so a turn
with no tool calls terminates instead of looping forever. Every branch of the
table is pinned here by construction, without invoking a model.
"""

from langchain_core.messages import HumanMessage

from agent.subagent import MAX_SEARCHES, MAX_STEPS, route_after_llm
from helpers import ai, call


def test_no_ai_message_goes_to_tool_results():
    assert route_after_llm({"messages": [HumanMessage(content="hi")]}) == "tool_results"


def test_toolless_turn_is_implicit_finish():
    # The model answering without calling a tool means "I'm done".
    state = {"messages": [ai(content="here is my answer")]}
    assert route_after_llm(state) == "tool_results"


def test_submit_findings_goes_to_process():
    state = {"messages": [ai([call("f", name="submit_findings")])]}
    assert route_after_llm(state) == "process_search_results"


def test_submit_findings_wins_over_search_in_same_turn():
    # Called together, the finish path takes precedence over dispatching the
    # search — order in the tool_calls list must not change the outcome.
    state = {
        "messages": [
            ai([call("s", name="exa_search"), call("f", name="submit_findings")])
        ]
    }
    assert route_after_llm(state) == "process_search_results"


def test_search_below_max_steps_goes_to_tool():
    state = {"messages": [ai([call("s")])], "steps": MAX_STEPS - 1}
    assert route_after_llm(state) == "tool"


def test_search_at_max_steps_hits_backstop():
    # Boundary: at exactly MAX_STEPS the loop stops rather than searching again.
    state = {"messages": [ai([call("s")])], "steps": MAX_STEPS}
    assert route_after_llm(state) == "tool_results"


def test_missing_steps_treated_as_zero():
    # No `steps` key yet -> 0, well below the backstop -> keep searching.
    state = {"messages": [ai([call("s")])]}
    assert route_after_llm(state) == "tool"


def test_search_at_ceiling_still_dispatches():
    # Boundary: the call that reaches MAX_SEARCHES is allowed to run.
    state = {"messages": [ai([call(str(i)) for i in range(MAX_SEARCHES)])]}
    assert route_after_llm(state) == "tool"


def test_search_past_ceiling_hits_backstop():
    # One over the ceiling is blocked, so the loop publishes what it gathered
    # rather than dispatching a search the budget does not cover.
    state = {"messages": [ai([call(str(i)) for i in range(MAX_SEARCHES + 1)])]}
    assert route_after_llm(state) == "tool_results"


def test_ceiling_counts_across_turns():
    # The count is over the whole history, not just the turn being routed.
    state = {"messages": [ai([call(str(i))]) for i in range(MAX_SEARCHES + 1)]}
    assert route_after_llm(state) == "tool_results"
