from pydantic import BaseModel, Field
from datetime import datetime


class ConversationBase(BaseModel):
    question: str = Field(..., description="用户问题")
    answer: str = Field(..., description="AI回答")


class ConversationCreate(ConversationBase):
    pass


class ConversationResponse(ConversationBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
