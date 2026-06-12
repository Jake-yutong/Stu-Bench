from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import episodes, providers, runs

app = FastAPI(title="Stu-Bench Demo API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "stu-bench-demo"}


app.include_router(episodes.router, prefix="/api/episodes", tags=["episodes"])
app.include_router(providers.router, prefix="/api/providers", tags=["providers"])
app.include_router(runs.router, prefix="/api/runs", tags=["runs"])
