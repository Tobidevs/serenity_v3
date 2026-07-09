from braintrust import EvalCase
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# ─────────────────────────────────────────────────────────────────────────
# EDGE CASE DATASET — Planner Decision Fidelity
#
# These 4 cases target gaps NOT covered by the basic-use-case dataset
# (PLANNER_DATASET). Each targets a specific, documented failure mode from
# PLAN_DECISION_FIDELITY_PROMPT rather than a generic routing scenario.
#
# Coverage map:
#   1. grounding_trap_well_known_verse        -> Dimension 3 (grounding), single-turn
#   2. grounding_trap_partial_citation_carryover -> Dimension 3 (grounding), multi-turn
#   3. clarification_citation_leak_temptation -> Dimension 1+3 (route + grounding via
#                                                 clarification_request), single-turn
#   4. false_bypass_trap_no_prior_answer      -> Dimension 1 (route), multi-turn,
#                                                 over_bypass_risk / fabrication risk
# ─────────────────────────────────────────────────────────────────────────

PLANNER_EDGE_CASE_DATASET = [
    {
        # A famous-enough verse (James 2:26) that a Planner leaning on training
        # data -- rather than treating itself as having no source of truth --
        # is tempted to just assert the citation instead of directing research
        # to find it. This is the Core Constraint in its purest, single-turn form.
        "messages": [
            HumanMessage(
                content="What's the exact wording of the verse that says faith without works is dead?"
            )
        ],
        "current_query": "What's the exact wording of the verse that says faith without works is dead?",
        "metadata": {
            "case_id": "grounding_trap_well_known_verse",
            "category": "grounding_trap",
            "expected_route": "continue_to_supervisor",
            "tests": (
                "Planner must NOT assert 'James 2:26' (or any book/chapter/verse) "
                "itself. The concept is well-known enough to tempt a training-data "
                "leak; refined_query and plan steps must direct research to find "
                "and confirm the citation, not assume it."
            ),
        },
        "expected": {
            "route": "continue_to_supervisor",
            "refined_query": (
                "User wants the exact wording of the specific Bible verse that "
                "expresses the idea that faith without accompanying works is dead "
                "or ineffective. The precise book, chapter, and verse have not "
                "been specified by the user and must be identified through "
                "research, not assumed."
            ),
            "clarification_request": "",
            "denominational_scope": "neutral_baseline",
            "plan": {
                "steps": [
                    {
                        "step_number": "1",
                        "tool": "subagent",
                        "step_name": "Identify the specific verse expressing this concept",
                        "description": (
                            "Search for the specific Bible verse or passage that "
                            "expresses the idea that faith without works is "
                            "dead/useless/ineffective, based on the concept "
                            "described by the user. Do not assume or assert a "
                            "specific book, chapter, or verse number -- identify "
                            "it through research."
                        ),
                    },
                    {
                        "step_number": "2",
                        "tool": "bible_api",
                        "step_name": "Retrieve exact verse text",
                        "description": (
                            "Once Step 1 identifies the specific verse(s), call "
                            "the Bible API to retrieve the exact wording for "
                            "accurate citation to the user."
                        ),
                    },
                ]
            },
        },
    },
    {
        # User carries a chapter number ("Romans 8") across turns but not the
        # verse. Tests the exact nuance the judge prompt calls out: carrying
        # forward a user-supplied fact is fine, but the Planner still cannot
        # supply the specific, not-yet-named verse number (38-39) itself.
        "messages": [
            HumanMessage(
                content="My small group is studying the book of Romans this month, chapter 8 I think."
            ),
            AIMessage(
                content="That's a rich chapter -- let me know if you'd like to dig into anything specific from it!"
            ),
            HumanMessage(
                content="Can you explain the verse about nothing being able to separate us from God's love?"
            ),
        ],
        "current_query": "Can you explain the verse about nothing being able to separate us from God's love?",
        "metadata": {
            "case_id": "grounding_trap_partial_citation_carryover",
            "category": "grounding_trap_multiturn",
            "expected_route": "continue_to_supervisor",
            "tests": (
                "'Romans 8' was named BY THE USER in a prior turn, so carrying "
                "it forward is not a violation. The specific verse numbers "
                "(38-39) were never supplied by the user and must not appear "
                "in refined_query or the plan -- only the research directive "
                "to locate them within the chapter the user already named."
            ),
        },
        "expected": {
            "route": "continue_to_supervisor",
            "refined_query": (
                "User is asking about a specific verse, likely within Romans "
                "chapter 8 (per earlier conversation), that expresses the idea "
                "that nothing can separate believers from the love of God. The "
                "user has named the chapter but not the exact verse number(s) "
                "-- the precise verse(s) must be identified through research "
                "within that chapter, not assumed."
            ),
            "clarification_request": "",
            "denominational_scope": "neutral_baseline",
            "plan": {
                "steps": [
                    {
                        "step_number": "1",
                        "tool": "subagent",
                        "step_name": "Locate the specific verse within Romans 8",
                        "description": (
                            "Search within Romans chapter 8 (as named by the "
                            "user in prior conversation) for the specific "
                            "verse(s) matching the concept that nothing can "
                            "separate believers from God's love. Do not assume "
                            "the exact verse number -- confirm it via research."
                        ),
                    },
                    {
                        "step_number": "2",
                        "tool": "bible_api",
                        "step_name": "Retrieve exact verse text",
                        "description": (
                            "Once the specific verse(s) are confirmed by Step 1, "
                            "call the Bible API to retrieve exact wording within "
                            "Romans 8 for citation."
                        ),
                    },
                ]
            },
        },
    },
    {
        # "The third day" is materially ambiguous (creation vs. resurrection) --
        # genuinely warrants ask_for_clarification -- but both branches have
        # famous, obvious citations attached, which is exactly the setup where
        # a Planner is tempted to smuggle an example verse into the
        # clarification question itself (explicitly flagged in the judge
        # prompt as a 0.0 grounding violation even when framed as an example).
        "messages": [
            HumanMessage(content="What's the theological significance of the third day?")
        ],
        "current_query": "What's the theological significance of the third day?",
        "metadata": {
            "case_id": "clarification_citation_leak_temptation",
            "category": "ambiguous_reference_grounding",
            "expected_route": "ask_for_clarification",
            "tests": (
                "clarification_request must name the two candidate TOPICS "
                "(creation account / Christ's resurrection) without citing "
                "specific verses (e.g. must NOT say 'Genesis 1' or "
                "'1 Corinthians 15:4') -- naming topics is scope-setting, "
                "naming verses as examples is a grounding violation."
            ),
        },
        "expected": {
            "route": "ask_for_clarification",
            "refined_query": (
                "User's query is materially ambiguous: 'the third day' could "
                "refer to the third day of creation, or to Christ's "
                "resurrection on the third day. These are entirely different "
                "research tasks, so clarification is needed before proceeding."
            ),
            "clarification_request": (
                "Are you asking about the third day in the creation account, "
                "or the third day in reference to Christ's resurrection?"
            ),
            "denominational_scope": "neutral_baseline",
            "plan": {"steps": []},
        },
    },
    {
        # User asks to "summarize what you told me," but the previous Serenity
        # turn was itself a clarification question, not a substantive answer.
        # Bypassing here would mean fabricating a summary of content that was
        # never actually generated -- the judge prompt treats an incorrect
        # bypass as the most serious route error since it risks an ungrounded
        # theological claim reaching the user.
        "messages": [
            HumanMessage(content="What does the Bible say about tithing?"),
            AIMessage(
                content=(
                    "Could you clarify -- are you asking about Old Testament "
                    "tithing law, or how tithing is typically taught and "
                    "practiced in churches today?"
                )
            ),
            HumanMessage(content="Just summarize what you told me."),
        ],
        "current_query": "Just summarize what you told me.",
        "metadata": {
            "case_id": "false_bypass_trap_no_prior_answer",
            "category": "route_boundary_bypass",
            "expected_route": "ask_for_clarification",
            "tests": (
                "There is no actual prior answer to reformat -- the previous "
                "turn was a clarification question. bypass_to_generation would "
                "be incorrect (over_bypass_risk / fabrication risk) since it "
                "would require inventing a theological claim on tithing that "
                "was never researched or stated. The original ambiguity is "
                "still unresolved."
            ),
        },
        "expected": {
            "route": "ask_for_clarification",
            "refined_query": (
                "User is asking for a summary of a prior answer, but "
                "Serenity's previous turn was a clarification question, not a "
                "substantive answer -- there is no research or claim to "
                "reformat. The original ambiguity about tithing (Old Testament "
                "law vs. modern church practice) is still unresolved and must "
                "be clarified before any research or response can proceed."
            ),
            "clarification_request": (
                "I haven't given you an answer on tithing yet -- I'd asked "
                "whether you meant Old Testament tithing law or how it's "
                "practiced in churches today. Which would you like me to look "
                "into?"
            ),
            "denominational_scope": "neutral_baseline",
            "plan": {"steps": []},
        },
    },
]


def build_planner_edge_case_dataset():
    return [
        EvalCase(
            input={
                "query": data["current_query"],
                "messages": data.get("messages", []),
            },
            expected=data.get("expected"),
            metadata=data.get("metadata"),
        )
        for data in PLANNER_EDGE_CASE_DATASET
    ]
