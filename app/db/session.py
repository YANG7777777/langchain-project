from sqlalchemy.orm import Session, sessionmaker
from .connection import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


"""
- 创建数据库会话工厂
- 提供 get_db 依赖注入函数
- 自动管理会话生命周期，确保连接正确关闭
"""