from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.db.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)

    question = Column(Text, nullable=False)

    answer = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Menu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)

    menu_name = Column(String(100), nullable=False, index=True)

    menu_code = Column(String(100), nullable=True, unique=True, index=True)

    parent_id = Column(Integer, nullable=True, index=True)

    menu_path = Column(String(255), nullable=True)

    menu_icon = Column(String(100), nullable=True)

    sort_order = Column(Integer, nullable=True, default=0)

    creator_id = Column(Integer, nullable=True)

    updater_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class RoleMenu(Base):
    __tablename__ = "role_menus"

    id = Column(Integer, primary_key=True, index=True)

    role_id = Column(Integer, nullable=False, index=True)

    menu_id = Column(Integer, nullable=False, index=True)

    creator_id = Column(Integer, nullable=True)

    updater_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String(50), nullable=False, unique=True, index=True)

    password = Column(String(255), nullable=False)

    email = Column(String(100), nullable=True, unique=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)

    dept_name = Column(String(100), nullable=False, unique=True, index=True)

    dept_code = Column(String(50), nullable=True, unique=True, index=True)

    parent_id = Column(Integer, nullable=True, index=True)

    parent_name = Column(String(100), nullable=True)

    creator_id = Column(Integer, nullable=True)

    updater_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False, index=True)

    gender = Column(String(10), nullable=True)

    birthday = Column(DateTime(timezone=True), nullable=True)

    phone = Column(String(20), nullable=True, index=True)

    dept_code = Column(String(50), nullable=True, index=True)

    department_name = Column(String(100), nullable=True)

    hire_date = Column(DateTime(timezone=True), nullable=True)

    confirmation_date = Column(DateTime(timezone=True), nullable=True)

    resignation_date = Column(DateTime(timezone=True), nullable=True)

    status = Column(Integer, nullable=True, index=True)

    salary = Column(Integer, nullable=True)

    education = Column(String(50), nullable=True)

    creator_id = Column(Integer, nullable=True)

    updater_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ClockRecord(Base):
    __tablename__ = "clock_records"

    id = Column(Integer, primary_key=True, index=True)

    employee_id = Column(Integer, nullable=False, index=True)

    employee_name = Column(String(100), nullable=True)

    clock_in_time = Column(DateTime(timezone=True), nullable=True)

    clock_out_time = Column(DateTime(timezone=True), nullable=True)

    date = Column(String(20), nullable=False, index=True)

    status = Column(Integer, nullable=True, default=0)

    remark = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())