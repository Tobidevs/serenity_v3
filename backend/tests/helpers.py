"""Message builders shared across the sub-agent unit tests.

Constructing LangChain messages inline makes the tests noisy and hides the one
field each case actually cares about. These keep the setup to a single line so
the assertion is what stands out.
"""

from langchain_core.messages import AIMessage, ToolMessage


def ai(tool_calls=None, content=""):
    """AIMessage with optional tool calls. No tool calls == a 'done' turn."""
    return AIMessage(content=content, tool_calls=tool_calls or [])


def call(call_id, name="exa_search", args=None):
    """A tool call entry as it appears on AIMessage.tool_calls."""
    return {"id": call_id, "name": name, "args": args or {}}


def tool(tool_call_id, name="exa_search", content="result"):
    """ToolMessage answering the call with the given id."""
    return ToolMessage(content=content, tool_call_id=tool_call_id, name=name)
