"""Run management API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Run
from app.schemas import RunCreateRequest, RunResponse, RunListResponse
from app.services.agent_service import agent_service

router = APIRouter(prefix="/api/runs", tags=["Runs"])


@router.get("", response_model=RunListResponse)
async def list_runs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve history of agent sandbox runs."""
    count_stmt = select(func.count(Run.id))
    total_count = (await db.execute(count_stmt)).scalar() or 0

    stmt = select(Run).order_by(Run.id.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    runs = result.scalars().all()

    return RunListResponse(
        items=[RunResponse.model_validate(r) for r in runs],
        total=total_count
    )


@router.post("", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def create_run(
    payload: RunCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Submit a task to execute in an isolated Celesto sandbox."""
    try:
        run_record = await agent_service.execute_run(
            db=db,
            task_description=payload.task_description,
            template_id=payload.template_id or "coding-agent",
            cpus=payload.cpus or 1,
            memory_mb=payload.memory_mb or 1024,
            disk_mb=payload.disk_mb or 15360,
            network_policy=payload.network_policy,
            execution_target=payload.execution_target or "celesto_sandbox",
        )
        return RunResponse.model_validate(run_record)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Run execution failed: {str(exc)}"
        )


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Fetch run details by run_id."""
    stmt = select(Run).where(Run.run_id == run_id)
    res = await db.execute(stmt)
    run_record = res.scalars().first()
    if not run_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found"
        )
    return RunResponse.model_validate(run_record)
