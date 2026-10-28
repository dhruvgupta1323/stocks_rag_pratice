from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class EvaluationResultRead(BaseModel):
    id: str
    run_id: str
    question_id: str
    category: str
    question_text: str
    expected_answer: str
    actual_answer: str
    retrieved_source_ids: List[str]
    metric_results: Dict[str, Any]
    failure_reason: Optional[str] = None
    latency_ms: float

    model_config = ConfigDict(from_attributes=True)


class EvaluationRunRead(BaseModel):
    id: str
    dataset_version: str
    model_version: str
    retrieval_configuration: Dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    summary_metrics: Dict[str, Any]
    results: Optional[List[EvaluationResultRead]] = None

    model_config = ConfigDict(from_attributes=True)


class RunEvaluationRequest(BaseModel):
    dataset_path: Optional[str] = None
    model_version: Optional[str] = "langgraph-agent-v1"

