from fastapi import APIRouter, Depends, Request
from app.dependencies.database import get_db
from sqlalchemy import text
from app.schemas.models import UserResponse, UserLoginRequest
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import bcrypt
import sys
print(f"Login.py: Python version: {sys.version}")
print(f"Login.py: Python path: {sys.path}")

# 尝试导入 jwt 模块
print("Login.py: Attempting to import jwt module...")
try:
    import jwt
    print(f"Login.py: jwt module imported successfully: {jwt}")
    print(f"Login.py: jwt module attributes: {dir(jwt)}")
    print(f"Login.py: Has encode attribute: {'encode' in dir(jwt)}")
except Exception as e:
    print(f"Login.py: Error importing jwt: {e}")

import datetime
from typing import Optional, Dict
from app.utils.crypto import rsa_decrypt, get_public_key_string

# JWT配置
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: Dict[str, str], expires_delta: Optional[datetime.timedelta] = None) -> str:
    print("Login.py: create_access_token called")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    print(f"Login.py: Data to encode: {to_encode}")
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        print(f"Login.py: Token generated successfully: {encoded_jwt}")
        return encoded_jwt
    except Exception as e:
        print(f"Login.py: Error generating token: {e}")
        raise

router = APIRouter(tags=["Login"])

ROLE_MAP = {
    0: "超管",
    1: "管理员",
    2: "用户"
}

def get_role_name(code: int) -> str:
    return ROLE_MAP.get(code, "用户")


# 获取RSA公钥
@router.get("/login/public-key", response_model=dict)
async def get_rsa_public_key():
    try:
        public_key = get_public_key_string()
        return {
            "status": "ok",
            "message": "获取公钥成功",
            "public_key": public_key
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取公钥失败: {str(e)}",
            "public_key": None
        }


# 用户登录
@router.post("/login", response_model=UserResponse)
async def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db)
):
    print("Login.py: Login request received")
    print(f"Login.py: Username: {request.username}")
    print(f"Login.py: Password: {request.password[:50]}...")

    try:
        print("Login.py: Querying user from database...")
        result = db.execute(
            text("SELECT id, username, password, email, role FROM users WHERE username = :username LIMIT 1"),
            {"username": request.username}
        )
        record = result.fetchone()

        print(f"Login.py: User record: {record}")
        if record is None:
            print("Login.py: User not found")
            return UserResponse(
                status="error",
                message="用户名或密码错误1",
                data=None
            )

        print(f"Login.py: User found: {record.username}")
        print(f"Login.py: Stored password: {record.password}")

        # 解密密码
        print("Login.py: Decrypting password...")
        try:
            decrypted_password = rsa_decrypt(request.password)
            print(f"Login.py: Decrypted password: {decrypted_password}")
        except Exception as e:
            print(f"Login.py: Decryption failed, using plain password: {e}")
            decrypted_password = request.password

        # 验证密码（bcrypt最大支持72字节，超过部分会被截断）
        print("Login.py: Verifying password...")
        truncated_password = decrypted_password[:72]
        print(f"Login.py: Truncated password: {truncated_password}")

        is_valid = bcrypt.checkpw(truncated_password.encode('utf-8'), record.password.encode('utf-8'))
        print(f"Login.py: Password validation result: {is_valid}")

        if not is_valid:
            print("Login.py: Password validation failed")
            return UserResponse(
                status="error",
                message="用户名或密码错误2",
                data=None
            )

        # 登录成功，生成JWT Token
        print("Login.py: Generating JWT token...")
        access_token = create_access_token(
            data={"sub": record.username, "user_id": str(record.id), "role": str(record.role)}
        )

        print(f"Login.py: Token generated: {access_token}")

        role_name = get_role_name(record.role) if record.role is not None else "用户"

        # 返回用户信息和Token
        print("Login.py: Returning success response")
        return UserResponse(
            status="ok",
            message="登录成功",
            data={
                "id": record.id,
                "userInfo": {
                    "username": record.username,
                    "email": record.email,
                    "role": record.role,
                    "role_name": role_name
                },
                "token": access_token
            }
        )

    except SQLAlchemyError as e:
        print(f"Login.py: Database error: {e}")
        return UserResponse(
            status="error",
            message=f"数据库查询失败: {str(e)}"
        )
    except Exception as e:
        print(f"Login.py: General error: {e}")
        import traceback
        traceback.print_exc()
        return UserResponse(
            status="error",
            message=f"登录失败: {str(e)}"
        )

# 用户退出登录
@router.post("/logout")
async def logout(request: Request):
    try:
        print("Login.py: Logout request received")

        return {
            "status": "ok",
            "message": "退出登录成功",
            "data": None
        }
    except Exception as e:
        print(f"Login.py: Logout error: {e}")
        return {
            "status": "error",
            "message": f"退出登录失败: {str(e)}",
            "data": None
        }
