'''
数据库初始化脚本，用于创建数据库表结构
用法：
  python3 init_db.py              # 创建所有表
  python3 init_db.py conversation  # 只创建 conversations 表
  python3 init_db.py user          # 只创建 users 表
  python3 init_db.py department    # 只创建 departments 表
  python3 init_db.py employee      # 只创建 employees 表
  python3 init_db.py menu          # 只创建 menus 表
  python3 init_db.py role_menu     # 只创建 role_menus 表
  python3 init_db.py conversation user department employee menu role_menu  # 创建指定的多个表
'''

import sys
from app.db.connection import engine
from app.db.base import Base
from app.models.conversation import Conversation, User, Department, Employee, Menu, RoleMenu


def create_conversation_table():
    Conversation.__table__.create(bind=engine, checkfirst=True)
    print("conversations 表创建成功！")


def create_user_table():
    User.__table__.create(bind=engine, checkfirst=True)
    print("users 表创建成功！")


def create_department_table():
    Department.__table__.create(bind=engine, checkfirst=True)
    print("departments 表创建成功！")


def create_employee_table():
    Employee.__table__.create(bind=engine, checkfirst=True)
    print("employees 表创建成功！")


def create_menu_table():
    Menu.__table__.create(bind=engine, checkfirst=True)
    print("menus 表创建成功！")


def create_role_menu_table():
    RoleMenu.__table__.create(bind=engine, checkfirst=True)
    print("role_menus 表创建成功！")


def init_db(tables=None):
    if tables is None or len(tables) == 0:
        create_conversation_table()
        create_user_table()
        create_department_table()
        create_employee_table()
        create_menu_table()
        create_role_menu_table()
        print("\n所有数据库表创建完成！")
    else:
        for table in tables:
            if table == "conversation":
                create_conversation_table()
            elif table == "user":
                create_user_table()
            elif table == "department":
                create_department_table()
            elif table == "employee":
                create_employee_table()
            elif table == "menu":
                create_menu_table()
            elif table == "role_menu":
                create_role_menu_table()
            else:
                print(f"未知的表名: {table}")
        print("\n指定的数据库表创建完成！")


if __name__ == "__main__":
    tables = sys.argv[1:] if len(sys.argv) > 1 else None
    init_db(tables)
