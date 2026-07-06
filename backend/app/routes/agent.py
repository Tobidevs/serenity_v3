import uuid

from fastapi import APIRouter
from pydantic import BaseModel

from agent.agent import graph

router = APIRouter(prefix="/agent", tags=["agent"])


class InvokeRequest(BaseModel):
    message: str
    thread_id: str | None = None


class InvokeResponse(BaseModel):
    messages: list


@router.post("/invoke", response_model=InvokeResponse)
def invoke_agent(request: InvokeRequest) -> InvokeResponse:
    # A thread_id is required by the checkpointer; generate one per request if
    # the client doesn't supply one (pass the same id back to continue a thread).
    config = {"configurable": {"thread_id": request.thread_id or str(uuid.uuid4())}}
    result = graph.invoke(
        {
            "messages": [{"role": "user", "content": request.message}],
            "current_query": request.message,
        },
        config=config,
    )
    return InvokeResponse(messages=result["messages"])
