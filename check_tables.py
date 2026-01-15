from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:yj%2312345@localhost:3306/myBlog")

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("SHOW TABLES"))
    tables = result.fetchall()
    print("myBlog 数据库中的表：")
    for table in tables:
        print(f"  - {table[0]}")
    
    if tables:
        print(f"\n共 {len(tables)} 个表")
    else:
        print("\n数据库中没有表")
