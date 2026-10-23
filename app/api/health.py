"""Health check API endpoint."""
from fastapi import APIRouter, Response, status
from app.config import settings
from app.database import check_db_health
from app.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def get_health(response: Response):
    """Health check verifying database and configuration state."""
    db_ok = await check_db_health()
    
    status_str = "healthy" if db_ok else "degraded"
    db_status = "connected" if db_ok else "disconnected"

    return HealthResponse(
        status=status_str,
        database=db_status,
        environment=settings.ENVIRONMENT,
        celesto_configured=settings.is_celesto_configured,
        llm_configured=settings.is_llm_configured
    )
