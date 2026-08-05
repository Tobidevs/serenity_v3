"""`_extract_search_trace` — the evidence the judge grades against.

The results no longer survive in the message history: once a report covers a
result set, the loop overwrites that ToolMessage with a short index. The trace
has to be rebuilt from the snapshot the loop takes instead, and the two sources
have to be combined in the right order — snapshot for searches that returned,
messages for searches that failed.
"""

from agent.evals.tasks import _extract_search_trace
from agent.subagent import STUB_MARKER
from helpers import ai, call, tool

RENDERED = "[1] TITLE: A Page\n    SOURCE: example.org\n    HIGHLIGHTS:\n      - the excerpt"
STUB = f"{STUB_MARKER}\nseen:\n  [1] A Page"


def _search(call_id, main="q"):
    return call(
        call_id,
        args={"main_query": main, "guiding_query": "g", "domain_scope": ["catholic"]},
    )


def test_excerpts_come_from_the_snapshot_not_the_stubbed_message():
    # The whole point. Grading against the message would show the judge an
    # index and score the report as uncited against evidence it cannot see.
    messages = [ai([_search("s1")]), tool("s1", content=STUB, id="t1")]
    trace, n = _extract_search_trace(
        messages, [{"tool_call_id": "s1", "results": RENDERED}]
    )

    assert "the excerpt" in trace
    assert STUB_MARKER not in trace
    assert n == 1


def test_query_arguments_are_paired_with_their_own_results():
    messages = [
        ai([_search("s1", main="first")]),
        tool("s1", content=STUB, id="t1"),
        ai([_search("s2", main="second")]),
        tool("s2", content=RENDERED, id="t2"),
    ]
    snapshot = [
        {"tool_call_id": "s1", "results": "[1] TITLE: One"},
        {"tool_call_id": "s2", "results": "[2] TITLE: Two"},
    ]

    trace, n = _extract_search_trace(messages, snapshot)

    assert n == 2
    first, second = trace.split("SEARCH 2")
    assert "first" in first and "One" in first
    assert "second" in second and "Two" in second


def test_a_failed_search_keeps_its_error_text():
    # A failed search is never rendered, so it contributes no snapshot entry.
    # The judge is told to forgive an empty yield, which it can only do if it
    # can see that the search failed rather than returned nothing.
    messages = [
        ai([_search("s1")]),
        tool("s1", content="ExaError: rate limited", id="t1"),
    ]

    trace, n = _extract_search_trace(messages, [])

    assert "ExaError: rate limited" in trace
    assert n == 1


def test_a_failed_search_does_not_shift_later_results():
    # The failure this keys on tool_call_id to avoid: pairing by position would
    # hand search 2's arguments the results that belong to search 3.
    messages = [
        ai([_search("s1", main="alpha")]),
        tool("s1", content=RENDERED, id="t1"),
        ai([_search("s2", main="beta")]),
        tool("s2", content="ExaError: boom", id="t2"),
        ai([_search("s3", main="gamma")]),
        tool("s3", content=RENDERED, id="t3"),
    ]
    # Only the two searches that returned appear in the snapshot.
    snapshot = [
        {"tool_call_id": "s1", "results": "results-for-alpha"},
        {"tool_call_id": "s3", "results": "results-for-gamma"},
    ]

    trace, n = _extract_search_trace(messages, snapshot)

    assert n == 3
    blocks = trace.split("SEARCH ")
    assert "results-for-alpha" in blocks[1] and "alpha" in blocks[1]
    assert "ExaError: boom" in blocks[2] and "beta" in blocks[2]
    assert "results-for-gamma" in blocks[3] and "gamma" in blocks[3]


def test_no_searches_gives_an_empty_trace():
    trace, n = _extract_search_trace([ai(content="done")], [])

    assert trace == ""
    assert n == 0
