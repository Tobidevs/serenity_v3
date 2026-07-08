import json
from braintrust import Literal, Score
from .planner_judge_prompts import PLAN_DECISION_FIDELITY_PROMPT, JUDGE_USER_PROMPT
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

class PlannerJudgeOutput(BaseModel):
    reasoning: str = Field(description="Step-by-step analysis, written before any verdict")
    route_verdict: Literal["correct", "defensible_but_suboptimal", "incorrect"] = Field(description="Verdict on whether the route/plan is correct")
    route_score: float = Field(description="Score for route correctness (0-1)")
    route_rationale: str = Field(description="Rationale for the route score")
    execution_verdict: Literal["excellent", "adequate", "needs_improvement", "poor"] = Field(description="Verdict on execution fidelity")
    execution_score: float = Field(description="Score for execution fidelity (0-1)")
    execution_rationale: str = Field(description="Rationale for the execution score")
    flags: list[str] = Field(description="List of execution issues or flags")
    grounding_verdict: Literal["grounded", "borderline", "violation"] = Field(description="Verdict on grounding fidelity")
    grounding_score: float = Field(description="Score for grounding fidelity (0-1)")
    grounding_rationale: str = Field(description="Rationale for the grounding score")
    grounding_flagged_items: list[str] = Field(description="List of grounding issues or flagged items")

model = init_chat_model(model_name="openai:gpt-5")
planner_judge_model = model.with_structured_output(PlannerJudgeOutput)


def planner_decision_fidelity(input, output, expected=None, metadata=None):
    user_prompt = JUDGE_USER_PROMPT.format(
        input=input,  # expects input.messages
        output=output,  # the PlannerOutput dict
        expected=(
            json.dumps(expected)
            if expected
            else "None provided — grade reference-free."
        ),
    )

    result = planner_judge_model.invoke(
        [
            SystemMessage(content=PLAN_DECISION_FIDELITY_PROMPT),
            HumanMessage(content=user_prompt),
        ]
    )

    return [
        Score(
            name="route_correctness",
            score=result["route_score"],
            metadata={
                "verdict": result["route_verdict"],
                "rationale": result["route_rationale"],
                "reasoning": result["reasoning"],
            },
        ),
        Score(
            name="execution_fidelity",
            score=result["execution_score"],
            metadata={
                "verdict": result["execution_verdict"],
                "rationale": result["execution_rationale"],
                "flags": result.get("flags", []),
            },
        ),
        Score(
            name="grounding_fidelity",
            score=result["grounding_score"],
            metadata={
                "verdict": result["grounding_verdict"],
                "rationale": result["grounding_rationale"],
                "flagged_items": result.get("grounding_flagged_items", []),
            },
        ),
    ]
