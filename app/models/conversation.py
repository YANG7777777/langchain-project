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


class User(Base):
    # 表名 ：映射到数据库中的 users 表
    __tablename__ = "users"

    # id ：主键，自增，带索引
    id = Column(Integer, primary_key=True, index=True)

    # username ：用户名，字符串类型，不能为空，唯一
    username = Column(String(50), nullable=False, unique=True, index=True)

    # password ：密码，字符串类型，不能为空（实际应用中应该加密存储）
    password = Column(String(255), nullable=False)

    # email ：邮箱，字符串类型，可以为空，唯一
    email = Column(String(100), nullable=True, unique=True, index=True)

    # created_at ：创建时间，默认当前时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # updated_at ：更新时间，默认当前时间，每次更新时自动更新
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Department(Base):
    # 表名 ：映射到数据库中的 departments 表
    __tablename__ = "departments"

    # id ：主键，自增，带索引
    id = Column(Integer, primary_key=True, index=True)

    # dept_name ：部门名称，字符串类型，不能为空，唯一
    dept_name = Column(String(100), nullable=False, unique=True, index=True)

    # dept_code ：部门编码，字符串类型，可以为空，唯一
    dept_code = Column(String(50), nullable=True, unique=True, index=True)

    # parent_id ：上级部门ID，整型，可以为空（用于树形结构）
    parent_id = Column(Integer, nullable=True, index=True)

    # parent_name ：上级部门名称，字符串类型，可以为空
    parent_name = Column(String(100), nullable=True)

    # creator_id ：创建人ID，整型，可以为空
    creator_id = Column(Integer, nullable=True)

    # updater_id ：修改人ID，整型，可以为空
    updater_id = Column(Integer, nullable=True)

    # created_at ：创建时间，默认当前时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # updated_at ：更新时间，默认当前时间，每次更新时自动更新
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
