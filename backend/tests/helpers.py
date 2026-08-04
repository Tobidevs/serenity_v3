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


def report(report_type="partial", findings="notes", call_id="r"):
    """A record_findings tool call. `report_type=None` omits the arg entirely."""
    args = {"findings": findings}
    if report_type is not None:
        args["report_type"] = report_type
    return call(call_id, name="record_findings", args=args)


def tool(tool_call_id, name="exa_search", content="result", id=None):
    """ToolMessage answering the call with the given id.

    `id` is what add_messages overwrites on, so any test about rewriting a
    message in place has to set it.
    """
    return ToolMessage(
        content=content, tool_call_id=tool_call_id, name=name, id=id
    )
