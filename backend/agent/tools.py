import json
import os
from typing import Literal

from dotenv import load_dotenv
from exa_py import Exa
from langchain_core.tools import tool

from agent.bible_api import fetch_passage
from lib.domains import DOMAIN_ALLOWLIST

load_dotenv()

exa = Exa(api_key=os.getenv("EXA_API_KEY"))


@tool
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
        num_results=5,
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
def think(thought: str):
    """Log a reasoning step and declare whether to keep searching or report."""
    return "Reasoning Logged."


@tool
def record_findings(
    report_type: Literal["partial", "full"],
    findings: str,
    next_steps: str = "",
):
    """Record what the searches returned so far, distilled to findings.

    Args:
        report_type: "partial" when the topic still has gaps and another search
            is coming, "full" when this is the finished report. A full report
            ends the run.
        findings: The report itself, formatted per the system prompt. On a
            partial this covers only the results just returned.
        next_steps: What the accompanying search is meant to close. Ignored on
            a full report.
    """
    return "Findings recorded."


@tool
def bible_passage(
    book: str,
    chapter: int,
    verse: int | None = None,
    start_verse: int | None = None,
    end_verse: int | None = None,
    translation: str | None = None,
) -> str:
    """Look up the text of a Bible passage by reference.

    Use `verse` on its own for a single verse, or `start_verse` and `end_verse`
    together for a multi-verse passage. Supplying neither returns the whole
    chapter.

    Args:
        book: Book name, e.g. "Genesis", "1 Corinthians", "Song of Songs".
        chapter: Chapter number.
        verse: Single verse to retrieve. Omit when requesting a range.
        start_verse: First verse of a multi-verse passage. Requires end_verse.
        end_verse: Last verse of a multi-verse passage. Requires start_verse.
        translation: Translation abbreviation such as "ESV", "NIV", or "KJV".
            Defaults to the configured translation when omitted.
    """
    return fetch_passage(book, chapter, verse, start_verse, end_verse, translation)


# results =  exa_search(main_query="What is the doctrine of the Trinity?", guiding_query="Explain the doctrine of the Trinity in Christian theology.", domain_scope=["primary_source"])

# print(results.results[0].title)
