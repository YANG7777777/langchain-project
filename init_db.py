'''
数据库初始化脚本，用于创建数据库表结构
'''

from app.db.connection import engine
from app.db.base import Base
from app.models.conversation import Conversation


def init_db():
    Base.metadata.create_all(bind=engine)
    print("数据库表创建成功！")


if __name__ == "__main__":
    init_db()
