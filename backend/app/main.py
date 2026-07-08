import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env and start Braintrust tracing before importing the agent graph, so
# auto_instrument patches LangChain/Anthropic before they are first used.
load_dotenv()

from app.tracing import setup_tracing

setup_tracing()

from app.routes import agent as agent_routes

app = FastAPI(title="Serenity Backend")

# Allow the Next.js frontend (a separate origin) to call the API from the
# browser. Override the allowed origins with CORS_ALLOW_ORIGINS (comma-sep).
_cors_origins = os.getenv(
    "CORS_ALLOW_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_routes.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
