from fastapi import FastAPI

from app.routes import agent as agent_routes

app = FastAPI(title="Serenity Backend")

app.include_router(agent_routes.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
