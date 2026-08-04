from agent.subagent import STUB_MARKER, search_subagent, build_user_message
from agent.prompts import SUBAGENT_SYSTEM_PROMPT
from agent.state import SubAgentState
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, ToolMessage
from app.tracing import setup_tracing

setup_tracing()


def test_search_subagent(query: str):
    result = search_subagent.invoke(
        {
            "messages": [
                SystemMessage(content=SUBAGENT_SYSTEM_PROMPT),
                HumanMessage(content=build_user_message(query)),
            ],
            "sources": [],
            "steps": 0,
            "findings": [],
            "final_sources": [],
            "partial_reports": [],
            "search_trace": [],
        }
    )
    return result


def summarize(result: dict) -> str:
    """What a run has to look like for the distillation loop to be working.

    The loop's whole claim is that raw excerpts leave the context once they
    have been reported on. That is invisible in the findings, so it is checked
    here against the message history the model actually saw on its last turn.
    """
    messages = result.get("messages", [])
    searches = sum(
        1
        for m in messages
        if isinstance(m, AIMessage)
        for c in m.tool_calls
        if c["name"] == "exa_search"
    )
    results = [
        m for m in messages if isinstance(m, ToolMessage) and m.name == "exa_search"
    ]
    stubbed = [m for m in results if str(m.content).startswith(STUB_MARKER)]

    return "\n".join(
        [
            f"turns:            {result.get('steps', 0)}",
            f"searches:         {searches}",
            f"result sets:      {len(results)} ({len(stubbed)} stubbed, "
            f"{len(results) - len(stubbed)} still raw)",
            f"partial reports:  {len(result.get('partial_reports', []))}",
            f"sources cited:    {len(result.get('final_sources', []))}",
            f"llm_error:        {result.get('llm_error') or 'none'}",
        ]
    )


if __name__ == "__main__":
    query = "What is catholic teaching on the Trinity?"
    result = test_search_subagent(query)

    print(summarize(result), "\n")
    for i, partial in enumerate(result.get("partial_reports", []), start=1):
        print(f"--- partial {i} ---\n{partial}\n")
    print("--- final findings ---")
    print("\n".join(result.get("findings", [])) or "(none)")
