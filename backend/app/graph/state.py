from typing import TypedDict, List, Dict, Any, Optional
from backend.app.schemas.research import CitationRead


class ResearchState(TypedDict):
    # Inputs
    question: str
    instrument_id: Optional[str]
    conversation_id: Optional[str]

    # Node 1: Resolved Stock & Instrument
    resolved_symbol: Optional[str]
    company_name: Optional[str]
    company_id: Optional[str]
    exchange: str

    # Node 2: Classification
    # Category: "price" | "technical" | "financial" | "news" | "comparison" | "unsupported" | "ambiguous"
    question_category: str
    requested_time_period: Optional[str]
    secondary_symbol: Optional[str]

    # Node 3: Market Data
    market_data: Optional[Dict[str, Any]]

    # Node 4: Financial Metrics
    financial_metrics: Optional[List[Dict[str, Any]]]

    # Node 5: Calculated Metrics
    calculated_analytics: Optional[Dict[str, Any]]

    # Node 6: News Results
    news_results: Optional[List[Dict[str, Any]]]

    # Node 7: Retrieved Research Records
    retrieved_evidence: Optional[List[Dict[str, Any]]]

    # Node 8 & 9: Citations & Answer Synthesis
    citations: List[Dict[str, Any]]
    direct_answer: str
    supporting_facts: List[str]
    explanations: Optional[str]
    evidence_sufficiency: str  # "sufficient" | "partial" | "insufficient"
    validation_errors: List[str]
    limitations: List[str]
    data_timestamps: Dict[str, Any]

    # Node 10: Final Output
    final_response: Optional[Dict[str, Any]]
    step_count: int

