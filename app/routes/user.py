from fastapi import APIRouter, Depends
from typing import Optional
from app.dependencies.database import get_db
from sqlalchemy import text
from app.schemas.models import UserResponse, UserListResponse, UserAddRequest, UserUpdateRequest
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(tags=["Users"])

ROLE_MAP = {
    0: "超管",
    1: "管理员",
    2: "员工"
}

def get_role_name(code: int) -> str:
    return ROLE_MAP.get(code, "员工")


# 获取用户详情
@router.get("/users/detail/{id}")
async def users_detail(
    id: int,
    db: Session = Depends(get_db)
):
    try:
        result = db.execute(
            text("""
                SELECT id, username, email, role,
                       DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                       DATE_FORMAT(updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
                FROM users WHERE id = :id LIMIT 1
            """),
            {"id": id}
        )
        record = result.fetchone()

        if record is None:
            return {
                "status": "ok",
                "message": "Database connected, but no record found",
                "data": None
            }

        return {
            "status": "ok",
            "message": "Database connection successful",
            "data": {
                "id": record.id,
                "username": record.username,
                "email": record.email,
                "role": record.role,
                "role_name": get_role_name(record.role),
                "created_at": record.created_at,
                "updated_at": record.updated_at
            }
        }

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


# 获取所有用户（支持按 id 和 username 过滤，支持分页）
@router.get("/users/all")
async def users_all(
    id: Optional[str] = None,
    username: Optional[str] = None,
    current: str = "1",
    pageSize: str = "10",
    db: Session = Depends(get_db)
):
    print('id, username, current, pageSize: ', id, username, current, pageSize)
    try:
        try:
            current_int = int(current)
            pageSize_int = int(pageSize)
        except (ValueError, TypeError):
            return {
                "status": "ok",
                "message": "Invalid pagination parameters",
                "data": {
                    "list": [],
                    "total": 0,
                    "current": 1,
                    "pageSize": 10
                }
            }

        id_int = None
        if id is not None:
            try:
                id_int = int(id)
            except (ValueError, TypeError):
                return {
                    "status": "ok",
                    "message": "Invalid id parameter",
                    "data": {
                        "list": [],
                        "total": 0,
                        "current": current_int,
                        "pageSize": pageSize_int
                    }
                }

        where_parts = ["WHERE 1=1"]
        params = {}

        if id_int is not None:
            where_parts.append("AND id = :id")
            params["id"] = id_int

        if username is not None:
            where_parts.append("AND username = :username")
            params["username"] = username

        where_clause = " ".join(where_parts)

        count_sql = f"SELECT COUNT(*) as total FROM users {where_clause}"
        count_result = db.execute(text(count_sql), params)
        total = count_result.fetchone().total

        offset = (current_int - 1) * pageSize_int

        data_sql = f"""
            SELECT id, username, email, role,
                   DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                   DATE_FORMAT(updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
            FROM users {where_clause}
            LIMIT :limit OFFSET :offset
        """
        params["limit"] = pageSize_int
        params["offset"] = offset

        result = db.execute(text(data_sql), params)
        records = result.fetchall()

        user_list = []
        for record in records:
            user_list.append({
                "id": record.id,
                "username": record.username,
                "email": record.email,
                "role": record.role,
                "role_name": get_role_name(record.role),
                "created_at": record.created_at,
                "updated_at": record.updated_at
            })

        return {
            "status": "ok",
            "message": "All users retrieved successfully",
            "data": {
                "list": user_list,
                "total": total,
                "current": current_int,
                "pageSize": pageSize_int
            }
        }

    except SQLAlchemyError as e:
        return {
            "status": "error",
            "message": f"Database query failed: {str(e)}",
            "data": None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "data": None
        }


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

        if request.email:
            check_email = db.execute(
                text("SELECT COUNT(*) as count FROM users WHERE email = :email"),
                {"email": request.email}
            )
            email_count = check_email.fetchone().count
            if email_count > 0:
                return UserResponse(
                    status="error",
                    message=f"Email {request.email} already exists",
                    data=None
                )

        password_hash = None
        if request.password:
            truncated_password = request.password[:72]
            password_hash = bcrypt.hashpw(truncated_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        role_value = request.role if request.role is not None else 2

        user_data = {
            "username": request.username,
            "password": password_hash,
            "email": request.email,
            "role": role_value,
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

        created_at_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
        updated_at_str = current_time.strftime("%Y-%m-%d %H:%M:%S")

        return UserResponse(
            status="ok",
            message="User added successfully",
            data={
                "id": result.lastrowid,
                "username": request.username,
                "email": request.email,
                "role": role_value,
                "role_name": get_role_name(role_value),
                "created_at": created_at_str,
                "updated_at": updated_at_str
            }
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

        password_hash = None
        if request.password:
            truncated_password = request.password[:72]
            password_hash = bcrypt.hashpw(truncated_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        update_data = {
            "username": request.username,
            "password": password_hash,
            "email": request.email,
            "role": request.role,
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

        updated_at_str = current_time.strftime("%Y-%m-%d %H:%M:%S")

        select_result = db.execute(
            text("""
                SELECT id, username, email, role,
                       DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at
                FROM users WHERE id = :id LIMIT 1
            """),
            {"id": id}
        )
        record = select_result.fetchone()

        return UserResponse(
            status="ok",
            message="User updated successfully",
            data={
                "id": id,
                "username": request.username,
                "email": request.email,
                "role": request.role,
                "role_name": get_role_name(request.role) if request.role is not None else None,
                "created_at": record.created_at if record else None,
                "updated_at": updated_at_str
            }
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
