import json

from braintrust import Score
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import Literal
from functools import lru_cache

from dotenv import load_dotenv

from agent.prompts import PLANNER_NODE_SYSTEM_PROMPT
from .planner_judge_prompts import PLAN_DECISION_FIDELITY_PROMPT, JUDGE_USER_PROMPT

load_dotenv()


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


@lru_cache(maxsize=1)
def _planner_judge_model():
    """Lazily build the structured judge model.

    Lazy + cached so importing this module doesn't require OPENAI_API_KEY at
    import time (eval_init imports this before tasks.py loads the .env).
    """
    model = init_chat_model("openai:gpt-5")
    return model.with_structured_output(PlannerJudgeOutput)


def _format_history(messages):
    if not messages:
        return "(no prior conversation)"
    lines = []
    for m in messages:
        role = getattr(m, "type", None) or (m.get("role") if isinstance(m, dict) else "user")
        content = getattr(m, "content", None) or (m.get("content") if isinstance(m, dict) else str(m))
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def planner_decision_fidelity(input, output, expected=None, metadata=None):
    user_prompt = JUDGE_USER_PROMPT.format(
        planner_system_prompt=PLANNER_NODE_SYSTEM_PROMPT,
        history=_format_history(input.get("messages")),
        route=output.get("route"),
        refined_query=output.get("refined_query"),
        clarification_request=output.get("clarification_request"),
        denominational_scope=output.get("denominational_scope"),
        plan=json.dumps(output.get("plan"), indent=2),
        expected=(
            json.dumps(expected, indent=2)
            if expected
            else "None provided \u2014 grade reference-free."
        ),
    )

    result: PlannerJudgeOutput = _planner_judge_model().invoke(
        [
            SystemMessage(content=PLAN_DECISION_FIDELITY_PROMPT),
            HumanMessage(content=user_prompt),
        ]
    )

    return [
        Score(
            name="route_correctness",
            score=result.route_score,
            metadata={
                "verdict": result.route_verdict,
                "rationale": result.route_rationale,
                "reasoning": result.reasoning,
            },
        ),
        Score(
            name="execution_fidelity",
            score=result.execution_score,
            metadata={
                "verdict": result.execution_verdict,
                "rationale": result.execution_rationale,
                "flags": result.flags,
            },
        ),
        Score(
            name="grounding_fidelity",
            score=result.grounding_score,
            metadata={
                "verdict": result.grounding_verdict,
                "rationale": result.grounding_rationale,
                "flagged_items": result.grounding_flagged_items,
            },
        ),
    ]
