import json
import os
from typing import Literal

from dotenv import load_dotenv
from exa_py import Exa
from langchain_core.tools import tool

from lib.domains import DOMAIN_ALLOWLIST

load_dotenv()

exa = Exa(api_key=os.getenv("EXA_API_KEY"))


@tool(response_format="content_and_artifact")
def exa_search(main_query: str, guiding_query: str, domain_scope: list[str]):
    """Search allowlisted theological sources for passages relevant to a query.

    Args:
        main_query: The search query used to retrieve documents.
        guiding_query: The question used to pull the most relevant highlights
            out of each retrieved document.
        domain_scope: Allowlist categories to search in addition to primary sources.
    """
    domains = []
    domains.extend(DOMAIN_ALLOWLIST["primary_source"])  # always include primary sources
    for domain in domain_scope:
        if domain in DOMAIN_ALLOWLIST:
            domains.extend(DOMAIN_ALLOWLIST[domain])

    result = exa.search(
        query=main_query,
        num_results=10,
        type="auto",
        include_domains=domains,
        contents={
            "highlights": {
                "query": guiding_query,
            }
        },
    )
    records = [
        {
            "title": r.title,
            "url": r.url,
            "favicon": r.favicon,
            "highlights": r.highlights,
        }
        for r in result.results
    ]
    return records


@tool
def think(thought: str, next_action: Literal["search_again", "stop_and_report"]):
    """Log a reasoning step and declare whether to keep searching or report."""
    return "Reasoning Logged."


@tool
def submit_findings():
    """Signal that research is complete and findings are ready to report."""
    pass


# results =  exa_search(main_query="What is the doctrine of the Trinity?", guiding_query="Explain the doctrine of the Trinity in Christian theology.", domain_scope=["primary_source"])

# print(results.results[0].title)
