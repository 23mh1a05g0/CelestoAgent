"""Main FastAPI entrypoint for the Celesto AI Agent Sandbox Platform."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.api import health_router, runs_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("celesto_platform")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle events."""
    logger.info("Initializing Celesto Agent Platform control plane...")
    try:
        await init_db()
        logger.info("Database initialized successfully.")
    except Exception as exc:
        logger.warning(f"Database initialization deferred (ledger service may still be starting): {exc}")
    yield
    logger.info("Shutting down Celesto Agent Platform control plane...")


app = FastAPI(
    title="Celesto AI Agent Sandbox Platform",
    description="Trusted control plane managing isolated microVM sandboxes, safety policies, and evaluation harnesses.",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(runs_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "Celesto AI Agent Sandbox Platform",
        "status": "online",
        "docs_url": "/docs",
        "endpoints": {
            "health": "/health",
            "runs": "/api/runs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
