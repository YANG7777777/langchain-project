from fastapi import APIRouter, Depends
from app.dependencies.database import get_db
from sqlalchemy import text
from app.schemas.models import UserResponse, UserListResponse, UserAddRequest, UserUpdateRequest
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(tags=["Users"])


# 获取用户详情
@router.get("/users/detail/{id}", response_model=UserResponse)
async def users_detail(
    id: int,
    db: Session = Depends(get_db)
):
    try:
        result = db.execute(text("SELECT * FROM users WHERE id = :id LIMIT 1"), {"id": id})
        record = result.fetchone()

        if record is None:
            return UserResponse(
                status="ok",
                message="Database connected, but no record found",
                data=None
            )
        
        return UserResponse(
            status="ok",
            message="Database connection successful",
            data={"id": record.id, "username": record.username, "email": record.email}
        )

    except SQLAlchemyError as e:
        return UserResponse(
            status="error",
            message=f"Database query failed: {str(e)}"
        )
    except Exception as e:
        return UserResponse(
            status="error",
            message=f"Unexpected error: {str(e)}"
        )


# 获取所有用户
@router.get("/users/all", response_model=UserListResponse)
async def users_all(
    db: Session = Depends(get_db)
):
    try:
        result = db.execute(text("SELECT id, username, email FROM users"))
        records = result.fetchall()

        if not records:
            return UserListResponse(
                status="ok",
                message="No users found",
                data=None
            )
        
        user_list = [{"id": record.id, "username": record.username, "email": record.email} for record in records]
        
        return UserListResponse(
            status="ok",
            message="All users retrieved successfully",
            data=user_list
        )

    except SQLAlchemyError as e:
        return UserListResponse(
            status="error",
            message=f"Database query failed: {str(e)}"
        )
    except Exception as e:
        return UserListResponse(
            status="error",
            message=f"Unexpected error: {str(e)}"
        )


# 新增用户
@router.post("/users/add", response_model=UserResponse)
async def users_add(
    request: UserAddRequest,
    db: Session = Depends(get_db)
):
    try:
        from datetime import datetime
        import bcrypt
        current_time = datetime.now()
        
        # 对密码进行哈希处理（bcrypt最大支持72字节，超过部分会被截断）
        password_hash = None
        if request.password:
            truncated_password = request.password[:72]
            password_hash = bcrypt.hashpw(truncated_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user_data = {
            "username": request.username,
            "password": password_hash,
            "email": request.email,
            "created_at": current_time,
            "updated_at": current_time
        }
        
        columns = []
        values = {}
        for key, value in user_data.items():
            if value is not None:
                columns.append(key)
                values[key] = value
        
        if not columns:
            return UserResponse(
                status="error",
                message="No valid data to insert",
                data=None
            )
        
        columns_str = ", ".join(columns)
        placeholders_str = ", ".join([f":{col}" for col in columns])
        sql = f"INSERT INTO users ({columns_str}) VALUES ({placeholders_str})"
        
        result = db.execute(text(sql), values)
        db.commit()
        
        return UserResponse(
            status="ok",
            message="User added successfully",
            data={"id": result.lastrowid, "username": request.username, "email": request.email}
        )
    except SQLAlchemyError as e:
        db.rollback()
        return UserResponse(
            status="error",
            message=f"Database query failed: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        return UserResponse(
            status="error",
            message=f"Unexpected error: {str(e)}"
        )


# 修改用户
@router.put("/users/update/{id}", response_model=UserResponse)
async def users_update(
    id: int,
    request: UserUpdateRequest,
    db: Session = Depends(get_db)
):
    try:
        from datetime import datetime
        import bcrypt
        current_time = datetime.now()
        
        # 对密码进行哈希处理（bcrypt最大支持72字节，超过部分会被截断）
        password_hash = None
        if request.password:
            truncated_password = request.password[:72]
            password_hash = bcrypt.hashpw(truncated_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        update_data = {
            "username": request.username,
            "password": password_hash,
            "email": request.email,
            "updated_at": current_time,
            "id": id
        }
        
        set_clauses = []
        values = {}
        for key, value in update_data.items():
            if value is not None and key != "id":
                set_clauses.append(f"{key} = :{key}")
                values[key] = value
        
        if not set_clauses:
            return UserResponse(
                status="ok",
                message="No data to update",
                data=None
            )
        
        values["id"] = id
        set_str = ", ".join(set_clauses)
        sql = f"UPDATE users SET {set_str} WHERE id = :id"
        
        result = db.execute(text(sql), values)
        db.commit()
        
        if result.rowcount == 0:
            return UserResponse(
                status="ok",
                message="User not found",
                data=None
            )
        
        return UserResponse(
            status="ok",
            message="User updated successfully",
            data={"id": id, "username": request.username, "email": request.email}
        )
    except SQLAlchemyError as e:
        db.rollback()
        return UserResponse(
            status="error",
            message=f"Database query failed: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        return UserResponse(
            status="error",
            message=f"Unexpected error: {str(e)}"
        )


# 删除用户
@router.delete("/users/delete/{id}", response_model=UserResponse)
async def users_delete(
    id: int,
    db: Session = Depends(get_db)
):
    try:
        result = db.execute(text("DELETE FROM users WHERE id = :id"), {"id": id})
        db.commit()
        
        if result.rowcount == 0:
            return UserResponse(
                status="ok",
                message="User not found",
                data=None
            )
        
        return UserResponse(
            status="ok",
            message="User deleted successfully",
            data={"id": id}
        )
    except SQLAlchemyError as e:
        db.rollback()
        return UserResponse(
            status="error",
            message=f"Database query failed: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        return UserResponse(
            status="error",
            message=f"Unexpected error: {str(e)}"
        )
