"""`_format_search_results` — the model-facing rendering of search hits.

The format exists so the model can tell one result from another and cite a
source by its number. The cases that matter are the ones that would corrupt
that: a missing field rendering as "None", a full url leaking into view, and
the numbering the citations point at.
"""

from agent.subagent import (
    NEXT_TURN_REMINDER,
    _format_search_results,
    _source_ledger,
    _stub_search_message,
)
from langchain_core.messages import ToolMessage


def _ledger(*urls):
    return _source_ledger([{"url": u} for u in urls])


def test_missing_title_degrades_to_placeholder():
    # A bare "None" in the text would read to the model as a real value.
    out = _format_search_results(
        [{"title": None, "url": "https://a.com/x", "highlights": ["h"]}],
        _ledger("https://a.com/x"),
    )

    assert "(no title)" in out
    assert "None" not in out


def test_absent_highlights_render_as_none_marker():
    # Empty list and a missing key both mean "this result had no excerpt".
    ledger = _ledger("u")
    empty = _format_search_results([{"title": "T", "url": "u", "highlights": []}], ledger)
    missing = _format_search_results([{"title": "T", "url": "u"}], ledger)

    assert "HIGHLIGHTS: (none)" in empty
    assert "HIGHLIGHTS: (none)" in missing


def test_each_highlight_becomes_its_own_bullet():
    out = _format_search_results(
        [{"title": "T", "url": "u", "highlights": ["first", "second"]}], _ledger("u")
    )

    assert "      - first" in out
    assert "      - second" in out


def test_full_url_is_never_shown_only_the_host():
    # The model cites numbers and the harness renders urls. A url it cannot see
    # is a url it cannot copy wrong.
    url = "https://www.newadvent.org/cathen/08573a.htm"
    out = _format_search_results([{"title": "T", "url": url}], _ledger(url))

    assert "SOURCE: newadvent.org" in out
    assert url not in out
    assert "/cathen/" not in out


def test_numbers_come_from_the_ledger_not_the_position():
    # The second search's first hit must not be another [1] — citations from an
    # earlier partial report still point at the original numbering.
    ledger = _ledger("a", "b", "c")
    out = _format_search_results([{"title": "C", "url": "c"}], ledger)

    assert "[3] TITLE: C" in out
    assert "[1]" not in out


def test_numbering_is_one_based():
    # Citations reference these numbers, so a 0-based index would silently
    # misattribute a source.
    out = _format_search_results(
        [{"title": "A", "url": "a"}, {"title": "B", "url": "b"}], _ledger("a", "b")
    )

    assert "[1] TITLE: A" in out
    assert "[2] TITLE: B" in out
    assert "[0]" not in out


def test_url_less_result_is_marked_uncitable():
    # It cannot be given a number, so it must not borrow one from a neighbour.
    out = _format_search_results(
        [{"title": "A", "url": "a"}, {"title": "B", "url": None}], _ledger("a")
    )

    assert "[1] TITLE: A" in out
    assert "[-] TITLE: B" in out
    assert "[2]" not in out


def test_results_close_with_the_next_turn_reminder():
    # The rule is in SUBAGENT_SYSTEM_PROMPT too, and the model ignores it there.
    # Restating it on the message read immediately before the decision is what
    # takes the fused report+search turn from 1/6 to 6/6.
    out = _format_search_results([{"title": "A", "url": "a"}], _ledger("a"))

    assert out.endswith(NEXT_TURN_REMINDER)


def test_reminder_offers_both_branches_not_just_the_fused_one():
    # A reminder that only ever said "call both" would never let the model emit
    # the lone full report that ends the run, burning the budget every time.
    assert 'report_type="partial"' in NEXT_TURN_REMINDER
    assert 'report_type="full"' in NEXT_TURN_REMINDER


def test_reminder_does_not_survive_stubbing():
    # Stubs are rebuilt from the "[n] TITLE:" lines alone, so the reminder drops
    # out on its own. If it ever leaked through, every stubbed result set would
    # carry a stale copy and the reminder would stop marking the live one.
    rendered = _format_search_results(
        [{"title": "A", "url": "a", "highlights": ["h"]}], _ledger("a")
    )
    stubbed = _stub_search_message(
        ToolMessage(content=rendered, tool_call_id="c1", name="exa_search", id="t1")
    )

    assert stubbed is not None
    assert NEXT_TURN_REMINDER not in stubbed.content
    assert "[1] A" in stubbed.content


def test_reminder_is_not_parsed_as_a_result_of_its_own():
    # It sits in the same message as the rendered hits, so any line looking like
    # a result head would show up in the stub as a phantom source.
    rendered = _format_search_results(
        [{"title": "A", "url": "a"}, {"title": "B", "url": "b"}], _ledger("a", "b")
    )
    stubbed = _stub_search_message(
        ToolMessage(content=rendered, tool_call_id="c1", name="exa_search", id="t1")
    )

    # Two results in, two lines out — the reminder adds none.
    assert len([ln for ln in stubbed.content.splitlines() if ln.startswith("  [")]) == 2
