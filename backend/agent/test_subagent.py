from agent.subagent import search_subagent, build_user_message
from agent.prompts import SUBAGENT_SYSTEM_PROMPT
from agent.state import SubAgentState
from langchain_core.messages import SystemMessage, HumanMessage
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
        }
    )
    return result


if __name__ == "__main__":
    query = "What is the significance of the number 7 in the Bible?"
    result = test_search_subagent(query)
    print("Final Findings:\n", result["findings"])
