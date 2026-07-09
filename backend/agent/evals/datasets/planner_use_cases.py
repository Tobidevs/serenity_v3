from braintrust import EvalCase
from langchain_core.messages import SystemMessage, HumanMessage

PLANNER_USE_CASE_DATASET = [
    {
        "messages": [
            HumanMessage(
                content="What verse or passage do catholics use to support the immaculate conception?"
            )
        ],
        "current_query": "What verse or passage do catholics use to support the immaculate conception?",
        "metadata": {
            "case_id": "catholic_immaculate_conception_scripture",
            "category": "scriptural_research",
            "expected_route": "continue_to_supervisor",
        },
        "expected": {
            "route": "continue_to_supervisor",
            "refined_query": (
                "What specific Bible verses or scriptural passages do Catholics cite "
                "in support of the doctrine of the Immaculate Conception?"
            ),
            "clarification_request": "",
            "denominational_scope": "denominational_support",
            "plan": {
                "steps": [
                    {
                        "step_number": "1",
                        "tool": "subagent",
                        "step_name": "Dispatch research subagent(s) on Catholic scriptural support",
                        "description": (
                            "Research what scriptural passages the Catholic tradition cites in "
                            "support of the Immaculate Conception doctrine. A single subagent "
                            "covering the Catholic position is sufficient; a second subagent may "
                            "optionally be dispatched to surface how the passages are read outside "
                            "that tradition,"
                        ),
                    },
                    {
                        "step_number": "2",
                        "tool": "bible_api",
                        "step_name": "Call Bible API on cited verses",
                        "description": (
                            "For each specific verse or passage identified by Step 1's research, "
                            "call the Bible API to retrieve its full text for accurate citation. "
                            "Do not call the Bible API on any verse that was not first surfaced by "
                            "Step 1's research."
                        ),
                    },
                ]
            },
        },
    },
    {
        "messages": [
            HumanMessage(content="What kinds of questions can you help me with?")
        ],
        "current_query": "What kinds of questions can you help me with?",
        "metadata": {
            "case_id": "meta_capabilities_question",
            "category": "meta_system",
            "expected_route": "bypass_to_generation",
        },
        "expected": {
            "route": "bypass_to_generation",
            "refined_query": "User is asking what topics and capabilities Serenity supports -- a meta question about the system itself, not a theological research question.",
            "clarification_request": "",
            "denominational_scope": "neutral_baseline",
            "plan": {"steps": []},
        },
    },
    {
        "messages": [HumanMessage(content="What does that verse mean?")],
        "current_query": "What does that verse mean?",
        "metadata": {
            "case_id": "ambiguous_verse_reference",
            "category": "ambiguous_reference",
            "expected_route": "ask_for_clarification",
        },
        "expected": {
            "route": "ask_for_clarification",
            "refined_query": "User's query is ambiguous because they did not specify which verse they are referring to. The system should ask for clarification.",
            "clarification_request": "Which verse or passage would you like me to explain?",
            "denominational_scope": "neutral_baseline",
            "plan": {"steps": []},
        },
    },
]


def build_planner_use_case_dataset():
    return [
        EvalCase(
            input={
                "query": data["current_query"],
                "messages": data.get("messages", []),
            },
            expected=data.get("expected"),
            metadata=data.get("metadata"),
        )
        for data in PLANNER_USE_CASE_DATASET
    ]
