from fastapi import APIRouter
from pydantic import BaseModel

from agent.agent import graph

router = APIRouter(prefix="/agent", tags=["agent"])


class InvokeRequest(BaseModel):
    message: str


class InvokeResponse(BaseModel):
    messages: list


@router.post("/invoke", response_model=InvokeResponse)
def invoke_agent(request: InvokeRequest) -> InvokeResponse:
    result = graph.invoke({"messages": [{"role": "user", "content": request.message}]})
    return InvokeResponse(messages=result["messages"])
