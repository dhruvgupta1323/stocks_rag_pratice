import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.conversation import Conversation, Message
from backend.app.db.base import utc_now


class ConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_conversation(
        self, conversation_id: Optional[str] = None, session_id: str = "default-user", instrument_id: Optional[str] = None
    ) -> Conversation:
        if conversation_id:
            stmt = select(Conversation).options(selectinload(Conversation.messages)).where(Conversation.id == conversation_id)
            res = await self.db.execute(stmt)
            conv = res.scalar_one_or_none()
            if conv:
                if instrument_id and conv.selected_instrument_id != instrument_id:
                    conv.selected_instrument_id = instrument_id
                    await self.db.commit()
                return conv

        # Create new conversation
        conv = Conversation(
            id=str(uuid.uuid4()),
            session_id=session_id,
            selected_instrument_id=instrument_id,
            created_at=utc_now(),
        )
        self.db.add(conv)
        await self.db.commit()
        await self.db.refresh(conv)
        return conv

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        citations: Optional[List[Dict[str, Any]]] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> Message:
        msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            citations=citations or [],
            metadata_json=metadata_json or {},
            created_at=utc_now(),
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def get_history(self, conversation_id: str, limit: int = 20) -> List[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

