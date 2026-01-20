from fastapi import APIRouter, Depends
from app.dependencies.database import get_db
from sqlalchemy import text
from app.schemas.models import UserResponse, UserLoginRequest
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import bcrypt
from app.utils.crypto import rsa_decrypt, get_public_key_string

router = APIRouter(tags=["Login"])


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
    try:
        # 根据用户名查询用户
        result = db.execute(
            text("SELECT id, username, password, email FROM users WHERE username = :username LIMIT 1"),
            {"username": request.username}
        )
        record = result.fetchone()

        print('123', record)
        if record is None:
            return UserResponse(
                status="error",
                message="用户名或密码错误1",
                data=None
            )
        
        print('1234request', request.password)
        print('1234record', record.password)

        # 解密密码
        try:
            # 尝试解密密码（如果是加密的）
            decrypted_password = rsa_decrypt(request.password)
            print('1234decrypted', decrypted_password)
        except Exception as e:
            # 如果解密失败，可能是明文密码（用于向后兼容）
            print(f'解密失败，使用明文密码: {e}')
            decrypted_password = request.password

        # 验证密码（bcrypt最大支持72字节，超过部分会被截断）
        truncated_password = decrypted_password[:72]
        if not bcrypt.checkpw(truncated_password.encode('utf-8'), record.password.encode('utf-8')):
            return UserResponse(
                status="error",
                message="用户名或密码错误2",
                data=None
            )
        
        # 登录成功，返回用户信息（不包含密码）
        return UserResponse(
            status="ok",
            message="登录成功",
            data={
                "id": record.id,
                "username": record.username,
                "email": record.email
            }
        )

    except SQLAlchemyError as e:
        return UserResponse(
            status="error",
            message=f"数据库查询失败: {str(e)}"
        )
    except Exception as e:
        return UserResponse(
            status="error",
            message=f"登录失败: {str(e)}"
        )