from dotenv import load_dotenv
from fastapi import FastAPI

# Load .env and start Braintrust tracing before importing the agent graph, so
# auto_instrument patches LangChain/Anthropic before they are first used.
load_dotenv()

from app.tracing import setup_tracing

setup_tracing()

from app.routes import agent as agent_routes

app = FastAPI(title="Serenity Backend")

app.include_router(agent_routes.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
