from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:yj%2312345@localhost:3306/myBlog"
)

engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true"
)

"""
- 配置数据库连接
- 从 .env 文件读取数据库配置
- 创建数据库引擎，支持 SQL 日志输出
"""