"""API.Bible client for the supervisor's scripture lookup.

`fetch_passage` is the entry point: it turns a human reference into an
API.Bible request and returns citation-ready text. It never raises. Every
failure — an unknown book, an unlicensed translation, a dead upstream — comes
back as a string beginning "Error:", so the model can read what went wrong and
correct itself rather than losing the run to an exception.

The book and translation keys it resolves against live in lib/bible_books.py.
"""

import logging
import os
import re
import time
from functools import lru_cache

import httpx

from lib.bible_books import DEFAULT_TRANSLATION, TRANSLATIONS, normalize_book

logger = logging.getLogger(__name__)

BASE_URL = "https://rest.api.bible/v1"
TIMEOUT_SECONDS = 15.0
MAX_ATTEMPTS = 3
RETRY_STATUSES = {429, 500, 502, 503, 504}

# API.Bible truncates a passage at 200 verses, and a truncated passage reads as
# complete to the model. Refuse over-long ranges instead.
MAX_PASSAGE_VERSES = 200

# Plain text keeps HTML out of the context window; titles and notes are dropped
# so what the model reads is only what it should quote.
PASSAGE_PARAMS = {
    "content-type": "text",
    "include-notes": "false",
    "include-titles": "false",
    "include-chapter-numbers": "false",
    "include-verse-numbers": "true",
    "include-verse-spans": "false",
}


@lru_cache(maxsize=1)
def get_client() -> httpx.Client:
    """Pooled client, built lazily so importing this module needs no key."""
    return httpx.Client(base_url=BASE_URL, timeout=TIMEOUT_SECONDS)


def resolve_reference(
    book: str,
    chapter: int,
    verse: int | None,
    start_verse: int | None,
    end_verse: int | None,
) -> tuple[str, str, str] | str:
    """Build `(endpoint, id, reference)` from the arguments, or an error string.

    A whole chapter has no verse IDs to join into a range, so it uses the
    chapters endpoint; everything verse-scoped uses passages. Both return the
    same shape. Rejections happen here rather than at a 404 so the message names
    what the model got wrong.
    """
    book_id = normalize_book(book)
    if book_id is None:
        return (
            f"Error: unknown book '{book}'. Use a standard book name such as "
            "'Genesis', 'Song of Songs', or '1 Corinthians'."
        )
    if chapter < 1:
        return f"Error: chapter must be a positive number, got '{chapter}'."

    has_range = start_verse is not None or end_verse is not None
    if verse is not None and has_range:
        return (
            "Error: pass either 'verse' for a single verse or "
            "'start_verse' and 'end_verse' for a passage, not both."
        )

    if verse is not None:
        if verse < 1:
            return f"Error: verse must be a positive number, got '{verse}'."
        return ("passages", f"{book_id}.{chapter}.{verse}", f"{book} {chapter}:{verse}")

    if has_range:
        if start_verse is None or end_verse is None:
            return (
                "Error: a verse range needs both 'start_verse' and 'end_verse'. "
                "For a single verse use 'verse' instead."
            )
        if start_verse < 1:
            return f"Error: start_verse must be a positive number, got '{start_verse}'."
        if start_verse > end_verse:
            return f"Error: start_verse ({start_verse}) is after end_verse ({end_verse})."
        if end_verse - start_verse + 1 > MAX_PASSAGE_VERSES:
            return (
                f"Error: range spans more than {MAX_PASSAGE_VERSES} verses, which "
                "the Bible API truncates. Request a smaller passage."
            )
        return (
            "passages",
            f"{book_id}.{chapter}.{start_verse}-{book_id}.{chapter}.{end_verse}",
            f"{book} {chapter}:{start_verse}-{end_verse}",
        )

    return ("chapters", f"{book_id}.{chapter}", f"{book} {chapter}")


def request_passage(
    endpoint: str, bible_id: str, resource_id: str, api_key: str
) -> httpx.Response | str:
    """GET a passage or chapter, retrying transient failures.

    Returns the response, or an error string once the failure is final. Retries
    cover the same ground as `with_llm_retry`: the network dropped, or the API
    asked us to come back later. Any other 4xx is returned as-is for the caller
    to translate, since replaying it would fail identically.
    """
    url = f"/bibles/{bible_id}/{endpoint}/{resource_id}"
    detail = "no response"

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = get_client().get(
                url, params=PASSAGE_PARAMS, headers={"api-key": api_key}
            )
            if response.status_code not in RETRY_STATUSES:
                return response
            detail = f"HTTP {response.status_code}"
        except httpx.HTTPError as exc:
            detail = type(exc).__name__

        logger.warning("Bible API %s (attempt %s/%s)", detail, attempt, MAX_ATTEMPTS)
        if attempt < MAX_ATTEMPTS:
            time.sleep(0.5 * 2 ** (attempt - 1))

    return (
        f"Error: Bible API unavailable ({detail}) after {MAX_ATTEMPTS} attempts. "
        "Passage could not be retrieved."
    )


def format_passage(data: dict, translation: str, reference: str) -> str:
    """Render a passage as citation-ready text, as _format_search_results does.

    The copyright line trails the text because the licensed translations
    require that attribution to travel with it.
    """
    # Collapse the text endpoint's padding without touching the wording, which
    # has to survive verbatim for the model to quote it. Spaces around newlines
    # go first, so a "\n \n \n" run still collapses to one blank line.
    text = re.sub(r"[ \t]+", " ", data.get("content") or "")
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return f"Error: {reference} ({translation}) returned no text."

    # Prefer the reference API.Bible echoes back — it describes what actually
    # came back rather than what we asked for.
    canonical = (data.get("reference") or reference).strip()
    attribution = re.sub(r"\s+", " ", data.get("copyright") or "").strip()

    parts = [f"{canonical} ({translation})", "", text]
    if attribution:
        parts += ["", f"— {attribution}"]
    return "\n".join(parts)


def fetch_passage(
    book: str,
    chapter: int,
    verse: int | None = None,
    start_verse: int | None = None,
    end_verse: int | None = None,
    translation: str | None = None,
) -> str:
    """Look up a passage and render it, or return an "Error: ..." string."""
    api_key = os.getenv("BIBLE_API_KEY")
    if not api_key:
        return (
            "Error: Bible API is not configured (BIBLE_API_KEY is unset). "
            "Scripture lookup is unavailable."
        )

    requested = (
        translation or os.getenv("BIBLE_API_DEFAULT_TRANSLATION", DEFAULT_TRANSLATION)
    ).strip().upper()
    bible_id = TRANSLATIONS.get(requested)
    if bible_id is None:
        return (
            f"Error: unknown translation '{requested}'. "
            f"Available: {', '.join(sorted(TRANSLATIONS))}."
        )

    resolved = resolve_reference(book, chapter, verse, start_verse, end_verse)
    if isinstance(resolved, str):
        return resolved
    endpoint, resource_id, reference = resolved

    result = request_passage(endpoint, bible_id, resource_id, api_key)
    if isinstance(result, str):
        return result

    status = result.status_code
    if status == 401:
        return "Error: Bible API rejected the credentials (401)."
    if status == 403:
        return (
            f"Error: this API key is not licensed for {requested}. "
            "Request a different translation."
        )
    if status == 404:
        return (
            f"Error: {reference} was not found in {requested}. Check the chapter "
            "and verse exist in this book, or try another translation if the "
            "book is deuterocanonical."
        )
    if status >= 400:
        return f"Error: Bible API rejected {reference} (HTTP {status})."

    try:
        data = result.json()["data"]
    except (ValueError, KeyError, TypeError):
        logger.exception("Unreadable Bible API payload for %s", reference)
        return f"Error: Bible API returned an unreadable response for {reference}."

    return format_passage(data, requested, reference)
