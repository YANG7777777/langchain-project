from typing import Optional

from pydantic import BaseModel, Field, EmailStr


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

class UserResponse(BaseModel):
    status: str = Field("ok", description="状态")
    message: str = Field(..., description="状态描述")
    data: Optional[dict] = Field(None, description="用户数据")

class UserListResponse(BaseModel):
    status: str = Field("ok", description="状态")
    message: str = Field(..., description="状态描述")
    data: Optional[list] = Field(None, description="用户列表")

class UserAddRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=1, max_length=50, description="用户名")
    password: Optional[str] = Field(None, min_length=6, max_length=255, description="密码")
    email: Optional[str] = Field(None, description="邮箱")

class UserUpdateRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=1, max_length=50, description="用户名")
    password: Optional[str] = Field(None, min_length=6, max_length=255, description="密码")
    email: Optional[str] = Field(None, description="邮箱")

class UserLoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=512, description="密码")

class DeepSeekResponse(BaseModel):
    answer: str = Field(..., description="回答内容")


class DeepSeekRequest(BaseModel):
    question: str = Field(..., min_length=1, description="用户问题")
    stream: bool = Field(False, description="是否流式返回")
