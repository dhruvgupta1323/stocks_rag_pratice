from typing import Literal, Dict, Any
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.graph.state import ResearchState
from backend.app.graph.nodes import (
    resolve_stock_node,
    classify_question_node,
    fetch_market_data_node,
    fetch_financial_data_node,
    calculate_metrics_node,
    search_news_disclosures_node,
    retrieve_stored_research_node,
    synthesize_answer_node,
    validate_evidence_node,
    finalize_response_node,
)


def route_after_classification(state: ResearchState) -> str:
    """Conditional router directing question to the minimal necessary data retrieval path."""
    cat = state.get("question_category", "price")
    if cat in ("unsupported", "ambiguous"):
        return "synthesize_answer"
    elif cat == "price":
        return "fetch_market_data"
    elif cat == "technical":
        return "fetch_market_data_for_technical"
    elif cat == "financial":
        return "fetch_financial_data"
    elif cat == "news":
        return "search_news_disclosures"
    elif cat == "comparison":
        return "fetch_market_data_for_comparison"
    return "fetch_market_data"


def create_research_graph(db: AsyncSession):
    """Compiles the bounded LangGraph state graph for stock intelligence."""
    workflow = StateGraph(ResearchState)

    # Wrap nodes requiring DB session
    async def _resolve_stock(state: ResearchState):
        return await resolve_stock_node(state, db)

    async def _fetch_market_data(state: ResearchState):
        return await fetch_market_data_node(state, db)

    async def _fetch_financial_data(state: ResearchState):
        return await fetch_financial_data_node(state, db)

    async def _search_news_disclosures(state: ResearchState):
        return await search_news_disclosures_node(state, db)

    async def _retrieve_stored_research(state: ResearchState):
        return await retrieve_stored_research_node(state, db)

    # Register nodes
    workflow.add_node("resolve_stock", _resolve_stock)
    workflow.add_node("classify_question", classify_question_node)
    workflow.add_node("fetch_market_data", _fetch_market_data)
    workflow.add_node("fetch_financial_data", _fetch_financial_data)
    workflow.add_node("calculate_metrics", calculate_metrics_node)
    workflow.add_node("search_news_disclosures", _search_news_disclosures)
    workflow.add_node("retrieve_stored_research", _retrieve_stored_research)
    workflow.add_node("synthesize_answer", synthesize_answer_node)
    workflow.add_node("validate_evidence", validate_evidence_node)
    workflow.add_node("finalize_response", finalize_response_node)

    # Set Entry Point
    workflow.set_entry_point("resolve_stock")
    workflow.add_edge("resolve_stock", "classify_question")

    # Conditional Routing
    workflow.add_conditional_edges(
        "classify_question",
        route_after_classification,
        {
            "synthesize_answer": "synthesize_answer",
            "fetch_market_data": "fetch_market_data",
            "fetch_market_data_for_technical": "fetch_market_data",
            "fetch_financial_data": "fetch_financial_data",
            "search_news_disclosures": "search_news_disclosures",
            "fetch_market_data_for_comparison": "fetch_market_data",
        },
    )

    # Market data can route to calculate_metrics if technical, or directly to synthesize
    def route_after_market_data(state: ResearchState) -> str:
        if state.get("question_category") == "technical":
            return "calculate_metrics"
        elif state.get("question_category") == "comparison":
            return "fetch_financial_data"
        return "synthesize_answer"

    workflow.add_conditional_edges(
        "fetch_market_data",
        route_after_market_data,
        {
            "calculate_metrics": "calculate_metrics",
            "fetch_financial_data": "fetch_financial_data",
            "synthesize_answer": "synthesize_answer",
        },
    )

    workflow.add_edge("calculate_metrics", "synthesize_answer")
    workflow.add_edge("fetch_financial_data", "synthesize_answer")
    workflow.add_edge("search_news_disclosures", "retrieve_stored_research")
    workflow.add_edge("retrieve_stored_research", "synthesize_answer")

    # Synthesis -> Guardrails Validation -> Finalize -> END
    workflow.add_edge("synthesize_answer", "validate_evidence")
    workflow.add_edge("validate_evidence", "finalize_response")
    workflow.add_edge("finalize_response", END)

    return workflow.compile()

