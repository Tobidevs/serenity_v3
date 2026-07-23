"""`_format_search_results` — the model-facing rendering of search hits.

The format exists so the model can tell one result from another and cite a
source by its number. The cases that matter are the ones that would corrupt
that: a missing field rendering as "None", and the numbering the citations
point at.
"""

from agent.subagent import _format_search_results


def test_missing_title_and_url_degrade_to_placeholders():
    # A bare "None" in the text would read to the model as a real value.
    out = _format_search_results([{"title": None, "url": None, "highlights": ["h"]}])

    assert "(no title)" in out
    assert "(no url)" in out
    assert "None" not in out


def test_absent_highlights_render_as_none_marker():
    # Empty list and a missing key both mean "this result had no excerpt".
    empty = _format_search_results([{"title": "T", "url": "u", "highlights": []}])
    missing = _format_search_results([{"title": "T", "url": "u"}])

    assert "HIGHLIGHTS: (none)" in empty
    assert "HIGHLIGHTS: (none)" in missing


def test_each_highlight_becomes_its_own_bullet():
    out = _format_search_results(
        [{"title": "T", "url": "u", "highlights": ["first", "second"]}]
    )

    assert "      - first" in out
    assert "      - second" in out


def test_numbering_is_one_based_and_increments():
    # Citations reference these numbers, so a 0-based or repeated index would
    # silently misattribute a source.
    out = _format_search_results(
        [{"title": "A", "url": "a"}, {"title": "B", "url": "b"}]
    )

    assert "[1] TITLE: A" in out
    assert "[2] TITLE: B" in out
    assert "[0]" not in out
