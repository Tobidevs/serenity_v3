"""Dropping raw search results once the model has reported on them.

The loop's premise is that a distilled report beats the excerpts it came from,
so reported-on results collapse to an index of numbers and titles. Two things
must hold or the design is unsafe: results the model has *not* reported on are
never dropped, and a stub never changes again once written — a stub that got
rewritten on a later turn would diverge from the cached prefix every turn.
"""

from agent.subagent import (
    STUB_MARKER,
    _reported_search_messages,
    _stub_search_message,
)
from helpers import ai, call, report, tool

RENDERED = (
    "[1] TITLE: Decree on Justification\n"
    "    SOURCE: newadvent.org\n"
    "    HIGHLIGHTS:\n"
    "      - a long excerpt that has now been distilled\n"
    "\n"
    "[2] TITLE: A Reformed Reply\n"
    "    SOURCE: ligonier.org\n"
    "    HIGHLIGHTS:\n"
    "      - another long excerpt"
)


def test_results_are_dropped_once_a_report_covers_them():
    messages = [
        ai([call("s1")]),
        tool("s1", id="t1"),
        ai([report("partial"), call("s2")]),
        tool("s2", id="t2"),
    ]

    dropped = [m.id for m in _reported_search_messages(messages)]

    assert dropped == ["t1"]


def test_unreported_results_are_never_dropped():
    # The invariant the whole design rests on. A turn that chains two searches
    # before reporting must keep both result sets in full.
    messages = [
        ai([call("s1")]),
        tool("s1", id="t1"),
        ai([call("s2")]),
        tool("s2", id="t2"),
    ]

    assert _reported_search_messages(messages) == []


def test_nothing_is_dropped_before_the_first_report():
    messages = [ai([call("s1")]), tool("s1", id="t1")]

    assert _reported_search_messages(messages) == []


def test_report_acks_are_not_treated_as_search_results():
    # record_findings gets a ToolMessage of its own. It is not a result set and
    # must not be stubbed.
    messages = [
        ai([call("s1")]),
        tool("s1", id="t1"),
        ai([report("partial"), call("s2")]),
        tool("r", name="record_findings", content="Findings recorded.", id="t_ack"),
        tool("s2", id="t2"),
        ai([report("partial"), call("s3")]),
    ]

    dropped = [m.id for m in _reported_search_messages(messages)]

    assert dropped == ["t1", "t2"]


def test_stub_keeps_every_number_and_title():
    # The model has to still know what it has seen, so it can go back for a
    # source a later search shows mattered after all.
    stubbed = _stub_search_message(tool("s1", content=RENDERED, id="t1"))

    assert stubbed.content == (
        f"{STUB_MARKER}\n"
        "seen:\n"
        "  [1] Decree on Justification\n"
        "  [2] A Reformed Reply"
    )


def test_stub_drops_the_excerpts():
    stubbed = _stub_search_message(tool("s1", content=RENDERED, id="t1"))

    assert "long excerpt" not in stubbed.content
    assert "HIGHLIGHTS" not in stubbed.content


def test_stub_reuses_the_id_so_it_overwrites_in_place():
    # add_messages keys on id; a new id would append a duplicate and leave the
    # original excerpts in history, defeating the point.
    original = tool("s1", content=RENDERED, id="t1")

    stubbed = _stub_search_message(original)

    assert stubbed.id == original.id
    assert stubbed.tool_call_id == original.tool_call_id


def test_stubbing_is_not_repeated():
    # A stub whose text changed on a later turn would break the cached prefix
    # from that position on every single turn.
    once = _stub_search_message(tool("s1", content=RENDERED, id="t1"))

    assert _stub_search_message(once) is None


def test_unrendered_content_is_left_alone():
    # A failed search reaches the model as its own error text and never gets
    # rendered, so there is nothing to index and the error must stay readable.
    error = tool("s1", content="ExaError: rate limited", id="t1")

    assert _stub_search_message(error) is None


def test_url_less_results_survive_in_the_index():
    rendered = "[-] TITLE: Untitled Page\n    SOURCE: (no source)\n    HIGHLIGHTS: (none)"

    stubbed = _stub_search_message(tool("s1", content=rendered, id="t1"))

    assert "[-] Untitled Page" in stubbed.content
