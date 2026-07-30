from braintrust import Score
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import Literal
from functools import lru_cache

from dotenv import load_dotenv

from .research_judge_prompts import RESEARCH_FIDELITY_PROMPT, RESEARCH_JUDGE_USER_PROMPT

load_dotenv()


class ResearchJudgeOutput(BaseModel):
    reasoning: str = Field(
        description="Step-by-step analysis, written before any verdict: what the topic needs, what the sub-agent searched, what the report delivered, and where they diverge"
    )

    # Dimension 1 — Search Strategy Efficiency
    search_strategy_verdict: Literal["efficient", "acceptable", "wasteful", "misdirected"] = Field(
        description="Verdict on the quality of the sub-agent's search decisions (domain_scope, query construction, budget discipline)"
    )
    search_strategy_rationale: str = Field(description="Rationale for the search strategy verdict")
    search_strategy_flags: list[str] = Field(
        description="Search-strategy issues, drawn only from: padded_domain_scope, missing_tradition_scope, wrong_domain_scope, invalid_domain_category, query_phrasing_conflated, thin_guiding_query, redundant_search, budget_wasted, premature_stop, no_search_issued"
    )

    # Dimension 2 — Context Recall
    context_recall_verdict: Literal["complete", "adequate", "partial", "inadequate"] = Field(
        description="Verdict on whether the report captured everything needed (relative to what search returned) and excluded the unnecessary"
    )
    context_recall_rationale: str = Field(description="Rationale for the context recall verdict")
    recall_gaps: list[str] = Field(
        description="Necessary, trace-supported findings the report dropped; report-format elements that are missing or malformed appear here under a 'format:' prefix"
    )
    recall_superfluous: list[str] = Field(
        description="Unnecessary or off-topic material the report included; report-format elements that should not be present appear here under a 'format:' prefix"
    )

    # Dimension 3 — Citation Integrity
    citation_integrity_verdict: Literal["sound", "minor_issues", "unsound", "fabrication"] = Field(
        description="Verdict on whether the report's claims are correctly and honestly sourced"
    )
    citation_integrity_rationale: str = Field(description="Rationale for the citation integrity verdict")
    citation_flagged_items: list[str] = Field(
        description="Exact offending spans, one entry per span, formatted \"<flag>: '<exact text>' — <why>\", with the flag drawn only from: uncited_claim, unresolvable_citation, fabricated_url, misrepresented_source, unsourced_fact"
    )


# The rubric's four-tier scale, keyed by verdict. Deriving the score here rather
# than asking the judge for a float makes verdict and score impossible to
# contradict, and pins every run to the same discrete scale. All twelve verdicts
# are distinct across the three dimensions, so one flat table is unambiguous.
VERDICT_SCORES = {
    "efficient": 1.0, "acceptable": 0.66, "wasteful": 0.33, "misdirected": 0.0,
    "complete": 1.0, "adequate": 0.66, "partial": 0.33, "inadequate": 0.0,
    "sound": 1.0, "minor_issues": 0.66, "unsound": 0.33, "fabrication": 0.0,
}


@lru_cache(maxsize=1)
def _research_judge_model():
    """Lazily build the structured judge model.

    Lazy + cached so importing this module doesn't require OPENAI_API_KEY at
    import time (eval_init imports this before tasks.py loads the .env).
    """
    model = init_chat_model("openai:gpt-5")
    return model.with_structured_output(ResearchJudgeOutput)


def research_fidelity(input, output, expected=None, metadata=None):
    user_prompt = RESEARCH_JUDGE_USER_PROMPT.format(
        topic=output.get("topic"),
        num_searches=output.get("num_searches"),
        search_trace=output.get("search_trace") or "(no searches were issued)",
        findings=output.get("findings") or "(no findings were submitted)",
        final_sources=output.get("final_sources"),
        llm_error=output.get("llm_error") or "(none)",
    )

    result: ResearchJudgeOutput = _research_judge_model().invoke(
        [
            SystemMessage(content=RESEARCH_FIDELITY_PROMPT),
            HumanMessage(content=user_prompt),
        ]
    )

    return [
        Score(
            name="search_strategy_efficiency",
            score=VERDICT_SCORES[result.search_strategy_verdict],
            metadata={
                "verdict": result.search_strategy_verdict,
                "rationale": result.search_strategy_rationale,
                "flags": result.search_strategy_flags,
                "reasoning": result.reasoning,
            },
        ),
        Score(
            name="context_recall",
            score=VERDICT_SCORES[result.context_recall_verdict],
            metadata={
                "verdict": result.context_recall_verdict,
                "rationale": result.context_recall_rationale,
                "gaps": result.recall_gaps,
                "superfluous": result.recall_superfluous,
            },
        ),
        Score(
            name="citation_integrity",
            score=VERDICT_SCORES[result.citation_integrity_verdict],
            metadata={
                "verdict": result.citation_integrity_verdict,
                "rationale": result.citation_integrity_rationale,
                "flagged_items": result.citation_flagged_items,
            },
        ),
    ]
