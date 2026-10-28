from typing import List, Dict, Any, Set
import numpy as np


class EvaluationMetrics:
    """Quantitative measurement formulas for retrieval, answer quality, and system reliability."""

    @staticmethod
    def calculate_retrieval_metrics(
        retrieved_ids: List[str], ground_truth_ids: List[str], k: int = 5
    ) -> Dict[str, float]:
        """Calculates Precision@K, Recall@K, and Mean Reciprocal Rank (MRR)."""
        if not ground_truth_ids:
            return {"precision_at_k": 1.0, "recall_at_k": 1.0, "mrr": 1.0}

        retrieved_k = retrieved_ids[:k]
        hits = set(retrieved_k).intersection(set(ground_truth_ids))

        precision = len(hits) / float(len(retrieved_k)) if retrieved_k else 0.0
        recall = len(hits) / float(len(ground_truth_ids))

        # Reciprocal Rank of first relevant document
        rr = 0.0
        for idx, doc_id in enumerate(retrieved_k):
            if doc_id in ground_truth_ids:
                rr = 1.0 / (idx + 1)
                break

        return {
            "precision_at_k": round(precision, 4),
            "recall_at_k": round(recall, 4),
            "mrr": round(rr, 4),
        }

    @staticmethod
    def calculate_answer_correctness(actual_text: str, expected_elements: List[str]) -> float:
        """Deterministic score measuring the coverage of essential factual elements in the answer."""
        if not expected_elements:
            return 1.0

        matches = sum(1 for elem in expected_elements if elem.lower() in actual_text.lower())
        return round(matches / float(len(expected_elements)), 4)

    @staticmethod
    def calculate_citation_metrics(
        citations: List[Dict[str, Any]], verified_source_ids: Set[str]
    ) -> Dict[str, float]:
        """Calculates citation precision and verifies hallucinated references."""
        if not citations:
            return {"citation_precision": 1.0, "hallucinated_citations_count": 0}

        valid_count = sum(1 for c in citations if str(c.get("source_id")) in verified_source_ids)
        precision = valid_count / float(len(citations))
        hallucinated = len(citations) - valid_count

        return {
            "citation_precision": round(precision, 4),
            "hallucinated_citations_count": hallucinated,
        }

    @staticmethod
    def calculate_latency_percentiles(latencies_ms: List[float]) -> Dict[str, float]:
        """Calculates P50, P90, P95, and average response latency."""
        if not latencies_ms:
            return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "avg": 0.0}

        arr = np.array(latencies_ms)
        return {
            "p50": round(float(np.percentile(arr, 50)), 2),
            "p90": round(float(np.percentile(arr, 90)), 2),
            "p95": round(float(np.percentile(arr, 95)), 2),
            "avg": round(float(np.mean(arr)), 2),
        }

