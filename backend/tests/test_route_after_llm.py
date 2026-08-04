"""`route_after_llm` — the loop's exit conditions.

Routing runs after the LLM turn rather than after the tool node, so a turn
with no tool calls terminates instead of looping forever. Turns are fused: a
report and the next search arrive together, so it is the report's
`report_type` — plus whether a search came with it — that decides whether the
loop continues. Every branch of the table is pinned here by construction,
without invoking a model.
"""

from langchain_core.messages import HumanMessage

from agent.subagent import MAX_SEARCHES, MAX_STEPS, route_after_llm
from helpers import ai, call, report


def test_no_ai_message_goes_to_tool_results():
    assert route_after_llm({"messages": [HumanMessage(content="hi")]}) == "tool_results"


def test_toolless_turn_is_implicit_finish():
    # The model answering without calling a tool means "I'm done".
    state = {"messages": [ai(content="here is my answer")]}
    assert route_after_llm(state) == "tool_results"


def test_full_report_goes_to_process():
    state = {"messages": [ai([report("full")])]}
    assert route_after_llm(state) == "process_search_results"


def test_full_report_wins_over_search_in_same_turn():
    # A full report ends the run even if the model contradicted itself by
    # searching alongside it. Order in the tool_calls list must not matter.
    state = {"messages": [ai([call("s"), report("full")])]}
    assert route_after_llm(state) == "process_search_results"


def test_full_report_wins_when_one_turn_carries_two_reports():
    # Parallel tool calls make this possible. Reading whichever came first
    # would let the partial keep the loop running while the full report's
    # text — the only copy of it — went nowhere.
    state = {
        "messages": [ai([report("partial", call_id="r1"), report("full", call_id="r2")])]
    }
    assert route_after_llm(state) == "process_search_results"


def test_partial_report_with_a_search_keeps_going():
    # The normal fused turn: bank what the last results were worth, go again.
    state = {"messages": [ai([report("partial"), call("s")])]}
    assert route_after_llm(state) == "tool"


def test_partial_report_without_a_search_ends_the_run():
    # "More to do" with nothing done about it. The next turn could only repeat
    # itself, so publish what has been banked.
    state = {"messages": [ai([report("partial")])]}
    assert route_after_llm(state) == "tool_results"


def test_malformed_report_type_is_treated_as_partial():
    # A missing or junk report_type must not end the run on a report the model
    # did not mean to finish; the caps still bound it.
    missing = {"messages": [ai([report(None), call("s")])]}
    junk = {"messages": [ai([report("FULL_REPORT"), call("s")])]}

    assert route_after_llm(missing) == "tool"
    assert route_after_llm(junk) == "tool"


def test_llm_error_wins_over_a_pending_report():
    # A failed call appends no message, so the latest AIMessage is the previous
    # turn's — already answered. Falling through would re-dispatch it.
    state = {"messages": [ai([report("partial"), call("s")])], "llm_error": "boom"}
    assert route_after_llm(state) == "tool_results"


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


def test_full_report_beats_the_ceiling():
    # A model that writes its report on the turn that busts the budget still
    # gets the report published rather than discarded for being one over.
    messages = [ai([call(str(i))]) for i in range(MAX_SEARCHES + 1)]
    messages.append(ai([report("full")]))

    assert route_after_llm({"messages": messages}) == "process_search_results"
