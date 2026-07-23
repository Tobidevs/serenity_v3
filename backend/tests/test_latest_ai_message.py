"""`_latest_ai_message` — finding the turn routing decisions key off.

Unlike the tool-message scoper, this must return the most recent AIMessage
whether or not it carried tool calls: a toolless turn is the model's implicit
"I'm done", and skipping back to an earlier tool-calling turn would hide it
and loop forever.
"""

from langchain_core.messages import HumanMessage

from agent.subagent import _latest_ai_message
from helpers import ai, call, tool


def test_returns_toolless_latest_turn_over_earlier_calling_turn():
    # The distinction from _current_turn_tool_messages: the toolless turn wins.
    done = ai(content="all done")
    messages = [ai([call("a")]), tool("a"), done]

    assert _latest_ai_message(messages) is done


def test_returns_none_when_no_ai_message():
    # Both callers null-check this, so None must be reachable.
    messages = [HumanMessage(content="hi"), tool("a")]

    assert _latest_ai_message(messages) is None


def test_not_confused_by_trailing_non_ai_messages():
    # A ToolMessage arriving after the AI turn must not shadow it.
    target = ai([call("a")])
    messages = [HumanMessage(content="q"), target, tool("a")]

    assert _latest_ai_message(messages) is target
