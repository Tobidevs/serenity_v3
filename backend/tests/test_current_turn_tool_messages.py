"""`_current_turn_tool_messages` — scoping tool results to the latest turn.

Correlation is by tool_call_id rather than list position, which is what keeps
a multi-call turn intact and stops an earlier turn's results from being
reprocessed on the next loop iteration.
"""

from langchain_core.messages import HumanMessage

from agent.subagent import _current_turn_tool_messages
from helpers import ai, call, tool


def test_empty_list_returns_empty():
    assert _current_turn_tool_messages([]) == []


def test_no_ai_with_tool_calls_returns_empty():
    # An AIMessage exists but never called a tool.
    messages = [HumanMessage(content="hi"), ai(content="just talking")]
    assert _current_turn_tool_messages(messages) == []


def test_returns_all_tool_messages_for_multi_call_turn():
    # One model turn issuing three tool calls at once must yield all three
    # answering ToolMessages, not just the first.
    messages = [
        HumanMessage(content="q"),
        ai([call("a"), call("b"), call("c")]),
        tool("a"),
        tool("b"),
        tool("c"),
    ]

    result = _current_turn_tool_messages(messages)

    assert {m.tool_call_id for m in result} == {"a", "b", "c"}


def test_excludes_prior_turns_tool_messages():
    # Regression: an earlier turn's results must not be reprocessed. Only the
    # ToolMessage matching the LATEST tool-calling AI turn is returned.
    messages = [ai([call("old")]), tool("old"), ai([call("new")]), tool("new")]

    result = _current_turn_tool_messages(messages)

    assert [m.tool_call_id for m in result] == ["new"]


def test_excludes_unmatched_tool_message():
    # A ToolMessage whose id matches no call in the latest turn is dropped.
    messages = [ai([call("a")]), tool("a"), tool("orphan")]

    result = _current_turn_tool_messages(messages)

    assert [m.tool_call_id for m in result] == ["a"]


def test_toolless_latest_turn_falls_back_to_last_calling_turn():
    # The most recent AIMessage has no tool calls (implicit finish), but an
    # earlier turn did call a tool. Scoping keys off the latest *tool-calling*
    # turn, so that turn's ToolMessages are still returned.
    messages = [ai([call("a")]), tool("a"), ai(content="all done")]

    result = _current_turn_tool_messages(messages)

    assert [m.tool_call_id for m in result] == ["a"]
