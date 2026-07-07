import os

from braintrust import auto_instrument, init_logger


def setup_tracing() -> None:
    """Wire up Braintrust tracing for the app.

    `init_logger` opens the logger that spans are written to, and
    `auto_instrument` patches the underlying LLM libraries (LangChain/LangGraph
    and the Anthropic client this agent uses) so their calls are traced without
    any per-call changes.

    No-op when BRAINTRUST_API_KEY is unset so local dev and tests can run
    without a Braintrust account.
    """
    api_key = os.getenv("BRAINTRUST_API_KEY")
    if not api_key:
        return

    init_logger(project="Serenity", api_key=api_key)
    auto_instrument()
