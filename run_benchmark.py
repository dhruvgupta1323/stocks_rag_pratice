import asyncio
import sys
import os

# Add root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app.core.logging import setup_logging
from backend.app.db.session import AsyncSessionLocal, init_db, close_db
from backend.app.evaluation.runner import EvaluationRunner


async def main():
    setup_logging()
    print("Initializing DB...")
    await init_db()
    async with AsyncSessionLocal() as db:
        runner = EvaluationRunner(db)
        print("Running benchmark evaluation suite against LangGraph AI pipeline...")
        run_record = await runner.run_benchmark()
        print("\n" + "=" * 60)
        print("BENCHMARK EVALUATION RESULTS")
        print("=" * 60)
        print(f"Run ID: {run_record.id}")
        print(f"Status: {run_record.status}")
        print(f"Summary Metrics:")
        for k, v in run_record.summary_metrics.items():
            print(f"  • {k}: {v}")
        print(f"\nQuestion Details ({len(run_record.results or [])} items):")
        for r in (run_record.results or []):
            status = "PASS" if not r.failure_reason else "FAIL"
            print(f"  [{status}] {r.question_id}: {r.question_text[:50]}... ({r.latency_ms} ms)")
            if r.failure_reason:
                print(f"         Reason: {r.failure_reason}")
                print(f"         Actual: {r.actual_answer}")
    await close_db()


if __name__ == "__main__":
    asyncio.run(main())
