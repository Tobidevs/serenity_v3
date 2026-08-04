"""`process_search_results` — the loop's publish step.

Three things have to hold here: `final_sources` is a citable list (deduped, no
entry that can't be cited), the report is recovered even when the run was cut
short before a full one was written, and the SOURCES block is built from the
harness's own ledger rather than from anything the model typed.
"""

from agent.subagent import process_search_results
from helpers import ai, report


def _state(sources=None, messages=None, partial_reports=None):
    """State for the node. `messages` is subscripted directly, so always set it."""
    return {
        "sources": sources or [],
        "messages": messages or [ai(content="done")],
        "partial_reports": partial_reports or [],
    }


def test_duplicate_urls_keep_first_occurrence():
    # `sources` appends across searches, so the same url recurs whenever two
    # searches surface it. First entry wins, so its title survives.
    sources = [
        {"title": "first", "url": "https://a.com"},
        {"title": "second", "url": "https://a.com"},
        {"title": "other", "url": "https://b.com"},
    ]

    result = process_search_results(_state(sources))

    assert [s["title"] for s in result["final_sources"]] == ["first", "other"]


def test_sources_without_url_are_dropped():
    # A source with no url can be neither deduped nor cited. It must also not
    # collapse together with other url-less entries or block real ones.
    sources = [
        {"title": "no url", "url": None},
        {"title": "empty url", "url": ""},
        {"title": "real", "url": "https://a.com"},
    ]

    result = process_search_results(_state(sources))

    assert [s["title"] for s in result["final_sources"]] == ["real"]


def test_raw_sources_list_is_not_mutated():
    # The raw list stays intact as the record of what every search returned.
    sources = [{"title": "a", "url": "https://a.com"}, {"title": "b", "url": "https://a.com"}]
    state = _state(sources)

    process_search_results(state)

    assert len(state["sources"]) == 2


def test_full_report_is_published():
    messages = [ai([report("full", findings="the text")])]

    result = process_search_results(_state(messages=messages))

    assert result["findings"] == ["the text"]


def test_partial_report_on_the_last_turn_is_not_taken_as_the_report():
    # A partial is working notes, not a finished article. It still reaches the
    # caller, but via the banked fallback rather than by being mistaken for a
    # full report — and if it were both, the text would be duplicated.
    messages = [ai([report("partial", findings="notes")])]

    result = process_search_results(_state(messages=messages, partial_reports=["notes"]))

    assert result["findings"] == ["notes"]


def test_banked_partials_are_published_when_no_full_report_was_written():
    # The budget ceiling, the MAX_STEPS backstop and an llm_error exit all
    # arrive with no full report. The research still done must not be thrown
    # away — this is the failure the old loop had.
    result = process_search_results(
        _state(messages=[ai(content="done")], partial_reports=["first", "second"])
    )

    assert result["findings"] == ["first\n\nsecond"]


def test_blank_partials_are_not_published_as_a_report():
    # Guards against emitting [""] — downstream would render it as a blank
    # section rather than as "this run found nothing".
    result = process_search_results(_state(partial_reports=["", "   "]))

    assert "findings" not in result


def test_implicit_finish_with_nothing_banked_publishes_sources_only():
    sources = [{"title": "a", "url": "https://a.com"}]

    result = process_search_results(_state(sources, [ai(content="done")]))

    assert result["final_sources"] == sources
    assert "findings" not in result


def test_sources_block_is_rendered_from_the_ledger():
    # The model never sees a url, so the block has to be built here. Numbers
    # follow first appearance in `sources`, which is the same order the model
    # was shown them in.
    sources = [
        {"title": "A", "url": "https://a.com"},
        {"title": "B", "url": "https://b.com"},
    ]
    messages = [ai([report("full", findings="claim one [1]\nclaim two [2]")])]

    findings = process_search_results(_state(sources, messages))["findings"][0]

    assert "SOURCES\n[1] https://a.com — A\n[2] https://b.com — B" in findings


def test_uncited_sources_get_no_entry():
    # A search hit the report never cites does not appear, matching the
    # prompt's rule and keeping the block to what the Supervisor can follow up.
    sources = [
        {"title": "A", "url": "https://a.com"},
        {"title": "B", "url": "https://b.com"},
    ]
    messages = [ai([report("full", findings="only this one matters [2]")])]

    findings = process_search_results(_state(sources, messages))["findings"][0]

    assert "[2] https://b.com — B" in findings
    assert "https://a.com" not in findings


def test_citation_of_a_number_that_was_never_issued_is_dropped():
    # There is no url to print for it. Rendering "[9] (unknown)" into the final
    # report would hand the Supervisor a citation it cannot resolve.
    sources = [{"title": "A", "url": "https://a.com"}]
    messages = [ai([report("full", findings="real [1] and invented [9]")])]

    findings = process_search_results(_state(sources, messages))["findings"][0]

    assert "[1] https://a.com — A" in findings
    assert "[9]" not in findings.split("SOURCES")[1]


def test_report_with_no_citations_gets_no_sources_block():
    sources = [{"title": "A", "url": "https://a.com"}]
    messages = [ai([report("full", findings="nothing usable came back")])]

    findings = process_search_results(_state(sources, messages))["findings"][0]

    assert findings == "nothing usable came back"
