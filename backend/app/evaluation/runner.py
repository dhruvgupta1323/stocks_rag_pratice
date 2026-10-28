import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.base import utc_now
from backend.app.models.evaluation import EvaluationRun, EvaluationResult
from backend.app.graph.workflow import create_research_graph
from backend.app.evaluation.metrics import EvaluationMetrics
from backend.app.schemas.evaluation import EvaluationRunRead, EvaluationResultRead


class EvaluationRunner:
    """Executes reproducible benchmark evaluations against the AI Stock Intelligence research pipeline."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_benchmark(
        self,
        dataset_path: Optional[str] = None,
        model_version: str = "langgraph-agent-v1",
    ) -> EvaluationRunRead:
        path = dataset_path or settings.EVALUATION_DATASET_PATH
        # Resolve path relative to current or backend dir
        if not os.path.exists(path):
            alt_path = os.path.join(os.path.dirname(__file__), "../../../data/evaluation/benchmark_dataset.json")
            if os.path.exists(alt_path):
                path = alt_path

        with open(path, "r", encoding="utf-8") as f:
            dataset = json.load(f)

        dataset_version = dataset.get("version", "1.0.0")
        questions = dataset.get("questions", [])

        # Create Evaluation Run
        run = EvaluationRun(
            id=str(uuid.uuid4()),
            dataset_version=dataset_version,
            model_version=model_version,
            retrieval_configuration={
                "data_provider": settings.DATA_PROVIDER,
                "llm_provider": settings.LLM_PROVIDER,
                "timeout_seconds": settings.REQUEST_TIMEOUT_SECONDS,
            },
            started_at=utc_now(),
            status="running",
            summary_metrics={},
        )
        self.db.add(run)
        await self.db.commit()

        graph = create_research_graph(self.db)
        latencies: List[float] = []
        correctness_scores: List[float] = []
        citation_precisions: List[float] = []
        failed_count = 0
        results_list: List[EvaluationResult] = []

        for item in questions:
            q_id = item["id"]
            q_text = item["question"]
            category = item.get("category", "general")
            expected_ans = item.get("expected_answer", "")
            expected_elems = item.get("expected_elements", [])

            start_t = time.perf_counter()
            failure_reason = None
            actual_text = ""
            retrieved_sources = []
            citations = []

            try:
                state_input = {
                    "question": q_text,
                    "instrument_id": item.get("target_symbol"),
                    "conversation_id": f"eval-{run.id}",
                    "step_count": 0,
                    "validation_errors": [],
                    "citations": [],
                    "limitations": [],
                }
                out = await graph.ainvoke(state_input)
                final = out.get("final_response") or {}
                actual_text = final.get("direct_answer", "") + " " + " ".join(final.get("supporting_facts", []))
                citations = final.get("citations", [])
                retrieved_sources = [c.get("source_id") for c in citations if c.get("source_id")]
            except Exception as e:
                logger.error(f"Error evaluating question {q_id}: {e}")
                failure_reason = f"Execution exception: {str(e)}"
                actual_text = "Execution Error"
                failed_count += 1

            latency = round((time.perf_counter() - start_t) * 1000.0, 2)
            latencies.append(latency)

            correctness = EvaluationMetrics.calculate_answer_correctness(actual_text, expected_elems)
            correctness_scores.append(correctness)

            cit_metrics = EvaluationMetrics.calculate_citation_metrics(citations, set(retrieved_sources))
            citation_precisions.append(cit_metrics["citation_precision"])

            if correctness < 0.4 and not failure_reason:
                failure_reason = f"Low factual elements coverage: {correctness * 100:.1f}% of expected elements matched."
                failed_count += 1

            eval_res = EvaluationResult(
                id=str(uuid.uuid4()),
                run_id=run.id,
                question_id=q_id,
                category=category,
                question_text=q_text,
                expected_answer=expected_ans,
                actual_answer=actual_text.strip(),
                retrieved_source_ids=retrieved_sources,
                metric_results={
                    "correctness_score": correctness,
                    "citation_precision": cit_metrics["citation_precision"],
                    "hallucinated_citations": cit_metrics["hallucinated_citations_count"],
                },
                failure_reason=failure_reason,
                latency_ms=latency,
            )
            self.db.add(eval_res)
            results_list.append(eval_res)

        # Compute Summary Metrics
        latency_stats = EvaluationMetrics.calculate_latency_percentiles(latencies)
        pass_rate = round(((len(questions) - failed_count) / float(len(questions))) * 100.0, 2) if questions else 0.0
        avg_correctness = round(float(sum(correctness_scores) / len(correctness_scores)), 4) if correctness_scores else 0.0
        avg_cit_prec = round(float(sum(citation_precisions) / len(citation_precisions)), 4) if citation_precisions else 1.0

        run.completed_at = utc_now()
        run.status = "completed"
        run.summary_metrics = {
            "total_questions": len(questions),
            "passed_questions": len(questions) - failed_count,
            "failed_questions": failed_count,
            "pass_rate_pct": pass_rate,
            "average_correctness": avg_correctness,
            "citation_precision": avg_cit_prec,
            "latency": latency_stats,
        }

        await self.db.commit()
        await self.db.refresh(run)

        # Load run with results
        stmt = select(EvaluationRun).options(selectinload(EvaluationRun.results)).where(EvaluationRun.id == run.id)
        res = await self.db.execute(stmt)
        completed_run = res.scalar_one()

        return EvaluationRunRead.model_validate(completed_run)

    async def get_run_by_id(self, run_id: str) -> Optional[EvaluationRunRead]:
        stmt = select(EvaluationRun).options(selectinload(EvaluationRun.results)).where(EvaluationRun.id == run_id)
        res = await self.db.execute(stmt)
        run = res.scalar_one_or_none()
        if not run:
            return None
        return EvaluationRunRead.model_validate(run)

    async def list_runs(self, limit: int = 10) -> List[EvaluationRunRead]:
        stmt = (
            select(EvaluationRun)
            .options(selectinload(EvaluationRun.results))
            .order_by(desc(EvaluationRun.started_at))
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        runs = res.scalars().all()
        return [EvaluationRunRead.model_validate(r) for r in runs]

