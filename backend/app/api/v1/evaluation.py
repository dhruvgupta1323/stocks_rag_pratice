from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.evaluation.runner import EvaluationRunner
from backend.app.schemas.evaluation import EvaluationRunRead, RunEvaluationRequest

router = APIRouter(prefix="/evaluation", tags=["Evaluation & Benchmarks"])


@router.post("/run", response_model=EvaluationRunRead)
async def run_evaluation_benchmark(
    req: RunEvaluationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Execute reproducible benchmark evaluation against the AI Stock Intelligence research pipeline."""
    runner = EvaluationRunner(db)
    return await runner.run_benchmark(
        dataset_path=req.dataset_path,
        model_version=req.model_version or "langgraph-agent-v1",
    )


@router.get("/runs", response_model=List[EvaluationRunRead])
async def list_evaluation_runs(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """List historical evaluation runs."""
    runner = EvaluationRunner(db)
    return await runner.list_runs(limit=limit)


@router.get("/runs/{run_id}", response_model=EvaluationRunRead)
async def get_evaluation_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed metrics and question-by-question breakdown for an evaluation run."""
    runner = EvaluationRunner(db)
    run = await runner.get_run_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Evaluation run '{run_id}' not found.")
    return run

