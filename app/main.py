"""Main FastAPI application entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import init_db
from app.db.seed import seed_database
from app.api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize database and seed baseline data on startup."""
    init_db()
    seed_database()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description=(
        "LangGraph, LangChain, FastAPI ve PostgreSQL destekli "
        "Multi-Agent Banking Assistant API servisi."
    ),
    lifespan=lifespan,
)

# Enable CORS for web frontend / interactive dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", tags=["Dashboard"], include_in_schema=False)
@app.get("/ui", tags=["Dashboard"], include_in_schema=False)
def serve_dashboard():
    """Serves the interactive banking chat dashboard."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "message": "Multi-Agent Banking Assistant API is active.",
        "docs_url": "/docs",
        "chat_endpoint": f"{settings.API_V1_PREFIX}/chat",
    }


@app.get("/api", tags=["Root"])
def root_metadata():
    """Root metadata endpoint pointing to docs and chat endpoints."""
    return {
        "message": "Multi-Agent Banking Assistant API is active.",
        "docs_url": "/docs",
        "dashboard_url": "/",
        "chat_endpoint": f"{settings.API_V1_PREFIX}/chat",
        "agents_endpoint": f"{settings.API_V1_PREFIX}/agents",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
