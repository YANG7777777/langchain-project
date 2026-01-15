from typing import Optional

from pydantic import BaseModel, Field


class BlogsResponse(BaseModel):
    status: str = Field("ok", description="状态")
    message: str = Field(..., description="状态描述")
    data: Optional[dict] = Field(None, description="额外数据")

class BlogsListResponse(BaseModel):
    status: str = Field("ok", description="状态")
    message: str = Field(..., description="状态描述")
    data: Optional[list] = Field(None, description="博客列表")

class BlogsAddRequest(BaseModel):
    title: str = Field(..., min_length=1, description="博客标题")
    content: str = Field(..., min_length=1, description="博客内容")

class BlogsUpdateRequest(BaseModel):
    title: str = Field(..., min_length=1, description="博客标题")
    content: str = Field(..., min_length=1, description="博客内容")

class BlogsDeleteRequest(BaseModel):
    id: int = Field(..., description="博客ID")

class DeepSeekResponse(BaseModel):
    answer: str = Field(..., description="回答内容")


class DeepSeekRequest(BaseModel):
    question: str = Field(..., min_length=1, description="用户问题")
    stream: bool = Field(False, description="是否流式返回")