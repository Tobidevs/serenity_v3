"""`bible_passage` — the supervisor's scripture lookup.

Two things are load-bearing. The reference the model describes has to become the
exact API.Bible path, because a passage returned for a *different* reference
still looks like a valid answer. And the tool never raises: every failure is a
string the model can read and correct, so a bad book name costs a retry rather
than the run.

No network — the pooled client is swapped for a fake that records its requests.
"""

import httpx
import pytest

from agent.bible_api import resolve_reference
from agent.tools import bible_passage

PAYLOAD = {
    "data": {
        "reference": "John 3:16",
        "content": "  [16]  For God so loved the world...  \n\n\n\n  ",
        "copyright": "Scripture quotations  taken from\nthe ESV.",
    }
}


class FakeClient:
    def __init__(self, *responses):
        self._responses = list(responses)
        self.calls = []

    def get(self, url, params=None, headers=None):
        self.calls.append({"url": url, "params": params, "headers": headers})
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def ok(payload=PAYLOAD):
    return httpx.Response(200, json=payload)


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("BIBLE_API_KEY", "test-key")
    monkeypatch.setenv("BIBLE_API_DEFAULT_TRANSLATION", "ESV")
    monkeypatch.setattr("agent.bible_api.time.sleep", lambda _: None)


def install(monkeypatch, *responses) -> FakeClient:
    client = FakeClient(*responses)
    monkeypatch.setattr("agent.bible_api.get_client", lambda: client)
    return client


def call(**kwargs) -> str:
    return bible_passage.invoke(kwargs)


# --- reference building ------------------------------------------------------


def test_single_verse_builds_a_passage_id():
    assert resolve_reference("John", 3, 16, None, None) == (
        "passages",
        "JHN.3.16",
        "John 3:16",
    )


def test_range_repeats_the_book_and_chapter_on_both_ends():
    # API.Bible joins two *full* verse IDs; "JHN.3.16-18" is not valid.
    assert resolve_reference("John", 3, None, 16, 18)[:2] == (
        "passages",
        "JHN.3.16-JHN.3.18",
    )


def test_chapter_only_uses_the_chapters_endpoint():
    # A whole chapter has no verse IDs to build a range from.
    assert resolve_reference("Psalms", 23, None, None, None)[:2] == (
        "chapters",
        "PSA.23",
    )


def test_verse_and_range_together_are_refused():
    assert "not both" in resolve_reference("John", 3, 16, 16, 18)


def test_half_a_range_is_refused_rather_than_guessed():
    # Completing it would return a passage the model did not ask for and could
    # not distinguish from the one it wanted.
    assert "both" in resolve_reference("John", 3, None, 16, None)
    assert "both" in resolve_reference("John", 3, None, None, 18)


def test_backwards_and_oversized_ranges_are_refused():
    assert "after" in resolve_reference("John", 3, None, 18, 16)
    # Past 200 verses the API truncates, and a truncated passage reads as
    # complete to the model.
    assert "smaller passage" in resolve_reference("Psalms", 119, None, 1, 250)


def test_bad_book_and_chapter_are_named_in_the_error():
    assert "Hezekiah" in resolve_reference("Hezekiah", 1, None, None, None)
    assert "positive number" in resolve_reference("John", 0, None, None, None)


# --- request shape -----------------------------------------------------------


def test_request_targets_the_resolved_path_and_sends_the_key(configured, monkeypatch):
    client = install(monkeypatch, ok())

    call(book="1 Cor.", chapter=13, start_verse=4, end_verse=7)

    (request,) = client.calls
    assert request["url"] == "/bibles/f421fe261da7624f-01/passages/1CO.13.4-1CO.13.7"
    assert request["headers"]["api-key"] == "test-key"
    # Plain text keeps HTML out of the model's context.
    assert request["params"]["content-type"] == "text"


def test_translation_argument_overrides_the_default(configured, monkeypatch):
    client = install(monkeypatch, ok())

    out = call(book="John", chapter=3, verse=16, translation="kjv")

    assert client.calls[0]["url"].startswith("/bibles/de4e12af7f28f599-01/")
    assert "(KJV)" in out


# --- formatting --------------------------------------------------------------


def test_output_leads_with_the_reference_and_trails_the_copyright(
    configured, monkeypatch
):
    install(monkeypatch, ok())

    out = call(book="John", chapter=3, verse=16)

    assert out.splitlines()[0] == "John 3:16 (ESV)"
    assert "For God so loved the world..." in out
    # Attribution must travel with the text for the licensed versions.
    assert out.endswith("— Scripture quotations taken from the ESV.")
    assert "\n\n\n" not in out


def test_empty_content_is_reported_rather_than_returned_as_a_passage(
    configured, monkeypatch
):
    install(monkeypatch, ok({"data": {"reference": "John 3:16", "content": "   "}}))

    assert call(book="John", chapter=3, verse=16).startswith("Error:")


# --- failure paths -----------------------------------------------------------


def test_missing_key_is_reported_without_a_request(monkeypatch):
    monkeypatch.delenv("BIBLE_API_KEY", raising=False)
    client = install(monkeypatch, ok())

    assert "BIBLE_API_KEY is unset" in call(book="John", chapter=3, verse=16)
    assert client.calls == []


def test_unknown_translation_lists_the_available_ones(configured, monkeypatch):
    install(monkeypatch, ok())

    out = call(book="John", chapter=3, verse=16, translation="NRSV")

    assert out.startswith("Error: unknown translation 'NRSV'")
    assert "ESV" in out and "KJV" in out


def test_unlicensed_translation_points_the_model_elsewhere(configured, monkeypatch):
    install(monkeypatch, httpx.Response(403))

    out = call(book="John", chapter=3, verse=16, translation="NIV")

    assert "not licensed for NIV" in out and "different translation" in out


def test_not_found_names_the_reference(configured, monkeypatch):
    install(monkeypatch, httpx.Response(404))

    out = call(book="Sirach", chapter=1, verse=1)

    # Deuterocanon missing from a Protestant Bible is the common cause.
    assert "Sirach 1:1" in out and "deuterocanonical" in out


def test_transient_failure_is_retried_then_succeeds(configured, monkeypatch):
    client = install(
        monkeypatch, httpx.Response(503), httpx.ConnectError("dropped"), ok()
    )

    out = call(book="John", chapter=3, verse=16)

    assert len(client.calls) == 3
    assert out.startswith("John 3:16 (ESV)")


def test_exhausted_retries_return_an_error_string_not_an_exception(
    configured, monkeypatch
):
    client = install(
        monkeypatch, httpx.Response(503), httpx.Response(503), httpx.Response(503)
    )

    out = call(book="John", chapter=3, verse=16)

    assert len(client.calls) == 3
    assert "Bible API unavailable (HTTP 503)" in out


def test_unreadable_payload_does_not_escape_as_an_exception(configured, monkeypatch):
    install(monkeypatch, httpx.Response(200, text="not json"))

    assert "unreadable response" in call(book="John", chapter=3, verse=16)
