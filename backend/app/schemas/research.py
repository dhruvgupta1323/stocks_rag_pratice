from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class CitationRead(BaseModel):
    source_id: str
    title: str
    publisher: str
    url: str
    published_at: datetime
    claim: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ResearchSourceRead(BaseModel):
    id: str
    company_id: Optional[str] = None
    source_type: str
    title: str
    publisher: str
    url: str
    published_at: datetime
    retrieved_at: datetime
    content_hash: str
    processing_status: str
    licensing_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ResearchRecordRead(BaseModel):
    id: str
    source_id: str
    company_id: str
    normalized_text: str
    extracted_entities: Dict[str, Any]
    metadata_json: Dict[str, Any]
    created_at: datetime
    source: Optional[ResearchSourceRead] = None

    model_config = ConfigDict(from_attributes=True)


class StockNewsResponse(BaseModel):
    symbol: str
    company_name: str
    total_articles: int
    articles: List[ResearchSourceRead]


class AskQuestionRequest(BaseModel):
    question: str
    instrument_id: Optional[str] = None
    conversation_id: Optional[str] = None
    session_id: Optional[str] = "default-user"


class AskQuestionResponse(BaseModel):
    conversation_id: str
    question: str
    direct_answer: str
    supporting_facts: List[str] = Field(default_factory=list)
    explanations: Optional[str] = None
    citations: List[CitationRead] = Field(default_factory=list)
    data_timestamps: Dict[str, Any] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)
    data_status: str = "verified"
    sufficiency: str = "sufficient"  # sufficient, partial, insufficient

