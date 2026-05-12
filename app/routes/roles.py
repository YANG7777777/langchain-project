from fastapi import APIRouter, Depends
from typing import Optional
from pydantic import BaseModel, Field
from app.dependencies.database import get_db
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(tags=["Roles"])


class RoleResponse(BaseModel):
    status: str = Field("ok", description="状态")
    message: str = Field(..., description="状态描述")
    data: Optional[dict] = Field(None, description="角色数据")


class RoleListResponse(BaseModel):
    status: str = Field("ok", description="状态")
    message: str = Field(..., description="状态描述")
    data: Optional[dict] = Field(None, description="角色列表")


class RoleAddRequest(BaseModel):
    role_name: str = Field(..., min_length=1, max_length=50, description="角色名称")
    role_code: Optional[int] = Field(None, description="角色代码")


class RoleUpdateRequest(BaseModel):
    role_name: Optional[str] = Field(None, min_length=1, max_length=50, description="角色名称")


# 获取所有角色
@router.get("/roles/all")
async def roles_all(
    id: Optional[int] = None,
    role_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        where_clauses = []
        params = {}

        if id is not None:
            where_clauses.append("id = :id")
            params["id"] = id

        if role_name is not None:
            where_clauses.append("role_name LIKE :role_name")
            params["role_name"] = f"%{role_name}%"

        where_sql = ""
        if where_clauses:
            where_sql = " WHERE " + " AND ".join(where_clauses)

        result = db.execute(
            text(f"""
                SELECT id, role_name, role_code, creator_id, updater_id,
                       DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                       DATE_FORMAT(updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
                FROM roles
                {where_sql}
                ORDER BY role_code ASC
            """),
            params
        )
        records = result.fetchall()

        role_list = []
        for record in records:
            role_list.append({
                "id": record.id,
                "role_name": record.role_name,
                "role_code": record.role_code,
                "creator_id": record.creator_id,
                "updater_id": record.updater_id,
                "created_at": record.created_at,
                "updated_at": record.updated_at
            })

        return {
            "status": "ok",
            "message": "All roles retrieved successfully",
            "data": {
                "list": role_list,
                "total": len(role_list)
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


# 获取角色详情
@router.get("/roles/detail/{id}")
async def roles_detail(
    id: int,
    db: Session = Depends(get_db)
):
    try:
        result = db.execute(
            text("""
                SELECT id, role_name, role_code, creator_id, updater_id,
                       DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                       DATE_FORMAT(updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
                FROM roles WHERE id = :id LIMIT 1
            """),
            {"id": id}
        )
        record = result.fetchone()

        if record is None:
            return {
                "status": "ok",
                "message": "Role not found",
                "data": None
            }

        return {
            "status": "ok",
            "message": "Role retrieved successfully",
            "data": {
                "id": record.id,
                "role_name": record.role_name,
                "role_code": record.role_code,
                "creator_id": record.creator_id,
                "updater_id": record.updater_id,
                "created_at": record.created_at,
                "updated_at": record.updated_at
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


# 新增角色
@router.post("/roles/add")
async def roles_add(
    request: RoleAddRequest,
    creator_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    try:
        from datetime import datetime
        current_time = datetime.now()

        check_result = db.execute(text("SELECT MAX(id) as max_id FROM roles"))
        max_id = check_result.fetchone().max_id or 0
        new_id = max_id + 1

        role_code = request.role_code if request.role_code is not None else new_id

        updater_id = creator_id + 1 if creator_id is not None else None

        sql = text("""
            INSERT INTO roles (id, role_name, role_code, creator_id, updater_id, created_at, updated_at)
            VALUES (:id, :role_name, :role_code, :creator_id, :updater_id, :created_at, :updated_at)
        """)

        result = db.execute(sql, {
            "id": new_id,
            "role_name": request.role_name,
            "role_code": role_code,
            "creator_id": creator_id,
            "updater_id": updater_id,
            "created_at": current_time,
            "updated_at": current_time
        })
        db.commit()

        created_at_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
        updated_at_str = current_time.strftime("%Y-%m-%d %H:%M:%S")

        return {
            "status": "ok",
            "message": "Role added successfully",
            "data": {
                "id": new_id,
                "role_name": request.role_name,
                "role_code": role_code,
                "creator_id": creator_id,
                "updater_id": updater_id,
                "created_at": created_at_str,
                "updated_at": updated_at_str
            }
        }

    except SQLAlchemyError as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Database query failed: {str(e)}",
            "data": None
        }
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "data": None
        }


# 修改角色
@router.put("/roles/update/{id}")
async def roles_update(
    id: int,
    request: RoleUpdateRequest,
    updater_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    try:
        from datetime import datetime
        current_time = datetime.now()

        update_data = {
            "role_name": request.role_name,
            "updater_id": updater_id,
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
            return {
                "status": "ok",
                "message": "No data to update",
                "data": None
            }

        values["id"] = id
        set_str = ", ".join(set_clauses)
        sql = f"UPDATE roles SET {set_str} WHERE id = :id"

        result = db.execute(text(sql), values)
        db.commit()

        if result.rowcount == 0:
            return {
                "status": "ok",
                "message": "Role not found",
                "data": None
            }

        updated_at_str = current_time.strftime("%Y-%m-%d %H:%M:%S")

        select_result = db.execute(
            text("""
                SELECT id, role_name, role_code, creator_id, updater_id,
                       DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at
                FROM roles WHERE id = :id LIMIT 1
            """),
            {"id": id}
        )
        record = select_result.fetchone()

        return {
            "status": "ok",
            "message": "Role updated successfully",
            "data": {
                "id": record.id,
                "role_name": record.role_name,
                "role_code": record.role_code,
                "creator_id": record.creator_id,
                "updater_id": updater_id,
                "created_at": record.created_at,
                "updated_at": updated_at_str
            }
        }

    except SQLAlchemyError as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Database query failed: {str(e)}",
            "data": None
        }
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "data": None
        }


# 删除角色
@router.delete("/roles/delete/{id}")
async def roles_delete(
    id: int,
    db: Session = Depends(get_db)
):
    try:
        check_result = db.execute(
            text("SELECT COUNT(*) as count FROM users WHERE role = (SELECT role_code FROM roles WHERE id = :id)"),
            {"id": id}
        )
        count = check_result.fetchone().count

        if count > 0:
            return {
                "status": "error",
                "message": f"Cannot delete role: {count} user(s) are using this role",
                "data": None
            }

        result = db.execute(text("DELETE FROM roles WHERE id = :id"), {"id": id})
        db.commit()

        if result.rowcount == 0:
            return {
                "status": "ok",
                "message": "Role not found",
                "data": None
            }

        return {
            "status": "ok",
            "message": "Role deleted successfully",
            "data": {"id": id}
        }

    except SQLAlchemyError as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Database query failed: {str(e)}",
            "data": None
        }
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "data": None
        }
