from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.services.research_service import ResearchService
from backend.app.services.conversation_service import ConversationService
from backend.app.graph.workflow import create_research_graph
from backend.app.schemas.research import AskQuestionRequest, AskQuestionResponse, ResearchSourceRead

router = APIRouter(prefix="/research", tags=["AI Research Assistant"])


@router.post("/ask", response_model=AskQuestionResponse)
async def ask_stock_question(
    req: AskQuestionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Ask a natural-language question about an Indian equity and receive an evidence-backed answer."""
    conv_service = ConversationService(db)
    conv = await conv_service.get_or_create_conversation(
        conversation_id=req.conversation_id,
        session_id=req.session_id or "default-user",
        instrument_id=req.instrument_id,
    )

    # Save user message
    await conv_service.add_message(
        conversation_id=conv.id,
        role="user",
        content=req.question,
    )

    # Run LangGraph Research Workflow
    graph = create_research_graph(db)
    state_input = {
        "question": req.question,
        "instrument_id": req.instrument_id,
        "conversation_id": conv.id,
        "step_count": 0,
        "validation_errors": [],
        "citations": [],
        "limitations": [],
    }

    output = await graph.ainvoke(state_input)
    final = output.get("final_response") or {}

    response = AskQuestionResponse(
        conversation_id=conv.id,
        question=req.question,
        direct_answer=final.get("direct_answer", ""),
        supporting_facts=final.get("supporting_facts", []),
        explanations=final.get("explanations"),
        citations=final.get("citations", []),
        data_timestamps=final.get("data_timestamps", {}),
        limitations=final.get("limitations", []),
        data_status=final.get("data_status", "verified"),
        sufficiency=final.get("sufficiency", "sufficient"),
    )

    # Save assistant response to conversation history
    await conv_service.add_message(
        conversation_id=conv.id,
        role="assistant",
        content=response.direct_answer,
        citations=[c.model_dump() for c in response.citations],
        metadata_json={
            "supporting_facts": response.supporting_facts,
            "data_status": response.data_status,
            "sufficiency": response.sufficiency,
        },
    )

    return response


@router.get("/sources/{source_id}", response_model=ResearchSourceRead)
async def get_research_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full attribution metadata for a research source."""
    service = ResearchService(db)
    return await service.get_source_by_id(source_id)


@router.get("/conversations/{conversation_id}/history")
async def get_conversation_history(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve chat history for a session."""
    conv_service = ConversationService(db)
    msgs = await conv_service.get_history(conversation_id)
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "citations": m.citations,
            "created_at": m.created_at.isoformat(),
            "metadata": m.metadata_json,
        }
        for m in msgs
    ]

