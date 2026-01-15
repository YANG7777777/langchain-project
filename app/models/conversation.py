from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.db.base import Base


class Conversation(Base):
    # 表名 ：映射到数据库中的 conversations 表
    __tablename__ = "conversations"

    # id ：主键，自增，带索引
    id = Column(Integer, primary_key=True, index=True)

    # question ：用户问题，文本类型，不能为空
    question = Column(Text, nullable=False)

    # answer ：AI 回答，文本类型，不能为空
    answer = Column(Text, nullable=False)

    # created_at ：创建时间，默认当前时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # updated_at ：更新时间，默认当前时间，每次更新时自动更新
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
