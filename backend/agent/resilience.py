"""Shared error handling for the agent's LLM calls.

Two layers, deliberately kept thin:

`with_llm_retry` wraps a model so transient API failures are retried with
exponential backoff before the call is considered lost. `safe_invoke` runs the
call and turns anything that still escapes into `LLMCallFailed`, logging it once
at the point of failure so nodes only have to decide how to degrade.

Note the Anthropic client does its own retrying underneath (`max_retries=2` by
default), so a call that exhausts MAX_ATTEMPTS here has been attempted several
times over. That is intentional belt-and-braces, not a bug — but it means a
genuinely dead API takes a while to give up, which is why callers degrade
gracefully rather than blocking on a result.
"""

import logging
from typing import Any, Callable

from anthropic import (
    APIConnectionError,
    InternalServerError,
    OverloadedError,
    RateLimitError,
)
from langchain_core.runnables import Runnable

logger = logging.getLogger(__name__)

# Failures worth another attempt: the network dropped, or the API asked us to
# come back later. APIConnectionError also covers APITimeoutError, which
# subclasses it. Everything else — a bad request, a missing or invalid API key,
# a malformed structured output — will fail identically on a retry, so those
# raise straight through to the caller's fallback.
RETRYABLE_EXCEPTIONS = (
    APIConnectionError,
    RateLimitError,
    InternalServerError,
    OverloadedError,
)

MAX_ATTEMPTS = 3


class LLMCallFailed(RuntimeError):
    """An LLM call failed and retrying it is not going to help.

    Carries the label of the call that failed so a node's fallback path can say
    which step gave up without digging through the traceback.
    """

    def __init__(self, label: str):
        self.label = label
        super().__init__(f"{label} LLM call failed")


def with_llm_retry(model: Runnable) -> Runnable:
    """Add retry-with-backoff to a model for transient API failures only.

    Applied at the factory, after `with_structured_output` / `bind_tools`, so
    the retry replays the whole configured call rather than a bare completion.
    Jittered backoff keeps concurrent sub-agents from retrying in lockstep and
    re-triggering the rate limit that failed them.
    """
    return model.with_retry(
        retry_if_exception_type=RETRYABLE_EXCEPTIONS,
        stop_after_attempt=MAX_ATTEMPTS,
        wait_exponential_jitter=True,
    )


def safe_invoke(
    build_model: Callable[[], Runnable], messages: list, *, label: str
) -> Any:
    """Invoke a model, raising `LLMCallFailed` if it cannot produce a result.

    Takes the model *factory* rather than a built model so that a client which
    can't even be constructed — no ANTHROPIC_API_KEY, a bad model id — fails the
    same way as a call that died mid-flight. Both are equally fatal to the node,
    and neither should escape as a raw exception.

    The catch is broad on purpose: the point is that no node loses its fallback
    path to an exception type we failed to anticipate. `logger.exception` records
    the original traceback here, so callers are free to handle `LLMCallFailed`
    without re-logging.
    """
    try:
        return build_model().invoke(messages)
    except Exception as exc:
        logger.exception("%s LLM call failed", label)
        raise LLMCallFailed(label) from exc
