import uuid

from fastapi import APIRouter
from langgraph.types import Command
from pydantic import BaseModel

from agent.agent import graph

router = APIRouter(prefix="/agent", tags=["agent"])


class InvokeRequest(BaseModel):
    message: str
    thread_id: str | None = None


class Message(BaseModel):
    role: str
    content: str


class InvokeResponse(BaseModel):
    thread_id: str
    # Human-facing text to show the user: either the agent's answer or, when the
    # planner needs more info, its clarification question.
    reply: str
    # True when `reply` is a clarification question; the client should send the
    # user's answer back with the same thread_id to resume.
    awaiting_clarification: bool
    messages: list[Message]


def _thread_is_paused(config: dict) -> bool:
    """True if this thread is paused on an interrupt() awaiting user input."""
    state = graph.get_state(config)
    return any(task.interrupts for task in state.tasks)


def _serialize_messages(messages: list) -> list[Message]:
    out: list[Message] = []
    for m in messages:
        # LangGraph stores LangChain message objects; map their type to a role.
        content = getattr(m, "content", "")
        role = "assistant" if getattr(m, "type", None) == "ai" else "user"
        out.append(Message(role=role, content=content if isinstance(content, str) else str(content)))
    return out


def _extract_reply(result: dict) -> tuple[str, bool]:
    """Pull a human-facing reply out of a graph result.

    When the graph paused to ask the user something, `__interrupt__` holds the
    clarification question — surface that and flag that we're awaiting an answer.
    Otherwise return the latest assistant message (empty until the supervisor /
    report-generation nodes are implemented).
    """
    interrupts = result.get("__interrupt__")
    if interrupts:
        return str(interrupts[0].value), True
    for m in reversed(result.get("messages", [])):
        if getattr(m, "type", None) == "ai":
            content = getattr(m, "content", "")
            return content if isinstance(content, str) else str(content), False
    return "", False


@router.post("/invoke", response_model=InvokeResponse)
def invoke_agent(request: InvokeRequest) -> InvokeResponse:
    # A thread_id is required by the checkpointer; generate one per request if
    # the client doesn't supply one (pass the same id back to continue a thread).
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # If a previous turn paused on a clarification question, this message is the
    # user's answer: resume the paused graph instead of starting a fresh run.
    if request.thread_id and _thread_is_paused(config):
        result = graph.invoke(Command(resume=request.message), config=config)
    else:
        result = graph.invoke(
            {
                "messages": [{"role": "user", "content": request.message}],
                "current_query": request.message,
            },
            config=config,
        )

    reply, awaiting_clarification = _extract_reply(result)
    return InvokeResponse(
        thread_id=thread_id,
        reply=reply,
        awaiting_clarification=awaiting_clarification,
        messages=_serialize_messages(result.get("messages", [])),
    )
