import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, Message, MessageRole


class ConversationMemory:
    def create_conversation(
        self,
        db: Session,
        *,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str,
    ) -> Conversation:
        conversation = Conversation(organization_id=organization_id, user_id=user_id, title=title)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    def get_or_create(
        self,
        db: Session,
        *,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID | None,
        title: str,
    ) -> Conversation:
        if conversation_id:
            conversation = db.get(Conversation, conversation_id)
            if conversation is None or conversation.organization_id != organization_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
            return conversation
        return self.create_conversation(db, organization_id=organization_id, user_id=user_id, title=title)

    def list_conversations(self, db: Session, *, organization_id: uuid.UUID, user_id: uuid.UUID) -> list[Conversation]:
        return list(
            db.scalars(
                select(Conversation)
                .where(Conversation.organization_id == organization_id, Conversation.user_id == user_id)
                .order_by(Conversation.updated_at.desc())
            )
        )

    def messages(self, db: Session, *, conversation_id: uuid.UUID, organization_id: uuid.UUID) -> list[Message]:
        conversation = db.get(Conversation, conversation_id)
        if conversation is None or conversation.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        return list(
            db.scalars(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.asc())
            )
        )

    def add_message(
        self,
        db: Session,
        *,
        conversation_id: uuid.UUID,
        organization_id: uuid.UUID,
        role: MessageRole,
        content: str,
        provider: str | None = None,
        model: str | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            organization_id=organization_id,
            role=role,
            content=content,
            provider=provider,
            model=model,
            token_count=len(content.split()),
        )
        db.add(message)
        conversation = db.get(Conversation, conversation_id)
        if conversation:
            conversation.title = conversation.title or content[:80]
        db.commit()
        db.refresh(message)
        return message

    def build_context(self, db: Session, *, conversation_id: uuid.UUID, organization_id: uuid.UUID, limit: int = 8) -> str:
        messages = self.messages(db, conversation_id=conversation_id, organization_id=organization_id)[-limit:]
        return "\n".join(f"{message.role.value}: {message.content}" for message in messages)


conversation_memory = ConversationMemory()
