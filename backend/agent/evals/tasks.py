
from langchain_core.messages import SystemMessage

from agent.prompts import PLANNER_NODE_SYSTEM_PROMPT
from ..nodes import _planner_model
from ..state import PlannerOutput

    

def planner_eval_task(input):
    result: PlannerOutput = _planner_model().invoke(
        [SystemMessage(content=PLANNER_NODE_SYSTEM_PROMPT), input["messages"]]
    )
    
    return {
        "route": result.route,
        "refined_query": result.refined_query or "",
        "clarification_request": result.clarification_request or "",
        "plan": result.plan,
    }