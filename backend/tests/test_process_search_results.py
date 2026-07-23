"""`process_search_results` — the loop's publish step.

Two things have to hold here: `final_sources` is a citable list (deduped, no
entry that can't be cited), and `findings` is present only when the model
actually submitted some. Both finish paths land on this node, so the common
case is arriving with no submit_findings call at all.
"""

from agent.subagent import process_search_results
from helpers import ai, call


def _state(sources=None, messages=None):
    """State for the node. `messages` is subscripted directly, so always set it."""
    return {"sources": sources or [], "messages": messages or [ai(content="done")]}


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


def test_submit_findings_is_published():
    messages = [ai([call("f", name="submit_findings", args={"findings": "the text"})])]

    result = process_search_results(_state(messages=messages))

    assert result["findings"] == ["the text"]


def test_empty_findings_arg_publishes_no_findings_key():
    # Guards against emitting [""] — an empty findings string is not a finding,
    # and downstream would render it as a blank section.
    messages = [ai([call("f", name="submit_findings", args={"findings": ""})])]

    result = process_search_results(_state(messages=messages))

    assert "findings" not in result


def test_implicit_finish_publishes_sources_without_findings():
    # The MAX_STEPS backstop and an implicit finish both arrive with no
    # submit_findings call. That is a normal exit, not an error: sources
    # gathered on the way still get published.
    sources = [{"title": "a", "url": "https://a.com"}]

    result = process_search_results(_state(sources, [ai(content="done")]))

    assert result["final_sources"] == sources
    assert "findings" not in result
