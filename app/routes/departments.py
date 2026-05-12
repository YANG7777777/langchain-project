from fastapi import APIRouter, Depends
from typing import Optional
from pydantic import BaseModel, Field
from app.dependencies.database import get_db
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(tags=["Departments"])


class DepartmentResponse(BaseModel):
    status: str = Field("ok", description="状态")
    message: str = Field(..., description="状态描述")
    data: Optional[dict] = Field(None, description="部门数据")


class DepartmentListResponse(BaseModel):
    status: str = Field("ok", description="状态")
    message: str = Field(..., description="状态描述")
    data: Optional[dict] = Field(None, description="部门列表")


class DepartmentAddRequest(BaseModel):
    dept_name: str = Field(..., min_length=1, max_length=100, description="部门名称")
    dept_code: Optional[str] = Field(None, max_length=50, description="部门编码")
    parent_id: Optional[int] = Field(None, description="上级部门ID")


class DepartmentUpdateRequest(BaseModel):
    dept_name: Optional[str] = Field(None, min_length=1, max_length=100, description="部门名称")
    dept_code: Optional[str] = Field(None, max_length=50, description="部门编码")
    parent_id: Optional[int] = Field(None, description="上级部门ID")


# 获取所有部门（支持按 id 和 dept_name 过滤）
@router.get("/departments/all")
async def departments_all(
    id: Optional[int] = None,
    dept_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        where_clauses = []
        params = {}

        if id is not None:
            where_clauses.append("d.id = :id")
            params["id"] = id

        if dept_name is not None:
            where_clauses.append("d.dept_name LIKE :dept_name")
            params["dept_name"] = f"%{dept_name}%"

        where_sql = ""
        if where_clauses:
            where_sql = " WHERE " + " AND ".join(where_clauses)

        result = db.execute(
            text(f"""
                SELECT d.id, d.dept_name, d.dept_code, d.parent_id, d.parent_name,
                       d.creator_id, d.updater_id,
                       DATE_FORMAT(d.created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                       DATE_FORMAT(d.updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
                FROM departments d
                {where_sql}
                ORDER BY d.id ASC
            """),
            params
        )
        records = result.fetchall()

        dept_list = []
        for record in records:
            dept_list.append({
                "id": record.id,
                "dept_name": record.dept_name,
                "dept_code": record.dept_code,
                "parent_id": record.parent_id,
                "parent_name": record.parent_name,
                "creator_id": record.creator_id,
                "updater_id": record.updater_id,
                "created_at": record.created_at,
                "updated_at": record.updated_at
            })

        return {
            "status": "ok",
            "message": "All departments retrieved successfully",
            "data": {
                "list": dept_list,
                "total": len(dept_list)
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


# 获取部门详情
@router.get("/departments/detail/{id}")
async def departments_detail(
    id: int,
    db: Session = Depends(get_db)
):
    try:
        result = db.execute(
            text("""
                SELECT id, dept_name, dept_code, parent_id, parent_name, creator_id, updater_id,
                       DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                       DATE_FORMAT(updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
                FROM departments WHERE id = :id LIMIT 1
            """),
            {"id": id}
        )
        record = result.fetchone()

        if record is None:
            return {
                "status": "ok",
                "message": "Department not found",
                "data": None
            }

        return {
            "status": "ok",
            "message": "Department retrieved successfully",
            "data": {
                "id": record.id,
                "dept_name": record.dept_name,
                "dept_code": record.dept_code,
                "parent_id": record.parent_id,
                "parent_name": record.parent_name,
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


# 新增部门
@router.post("/departments/add")
async def departments_add(
    request: DepartmentAddRequest,
    creator_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    try:
        from datetime import datetime
        current_time = datetime.now()

        if request.dept_name:
            check_result = db.execute(
                text("SELECT COUNT(*) as count FROM departments WHERE dept_name = :dept_name"),
                {"dept_name": request.dept_name}
            )
            count = check_result.fetchone().count
            if count > 0:
                return {
                    "status": "error",
                    "message": f"Department name '{request.dept_name}' already exists",
                    "data": None
                }

        if request.dept_code:
            check_result = db.execute(
                text("SELECT COUNT(*) as count FROM departments WHERE dept_code = :dept_code"),
                {"dept_code": request.dept_code}
            )
            count = check_result.fetchone().count
            if count > 0:
                return {
                    "status": "error",
                    "message": f"Department code '{request.dept_code}' already exists",
                    "data": None
                }

        parent_name = None
        if request.parent_id is not None:
            parent_result = db.execute(
                text("SELECT dept_name FROM departments WHERE id = :parent_id LIMIT 1"),
                {"parent_id": request.parent_id}
            )
            parent_record = parent_result.fetchone()
            if parent_record:
                parent_name = parent_record.dept_name
            else:
                return {
                    "status": "error",
                    "message": f"Parent department with id {request.parent_id} not found",
                    "data": None
                }

        updater_id = creator_id + 1 if creator_id is not None else None

        sql = text("""
            INSERT INTO departments (dept_name, dept_code, parent_id, parent_name, creator_id, updater_id, created_at, updated_at)
            VALUES (:dept_name, :dept_code, :parent_id, :parent_name, :creator_id, :updater_id, :created_at, :updated_at)
        """)

        result = db.execute(sql, {
            "dept_name": request.dept_name,
            "dept_code": request.dept_code,
            "parent_id": request.parent_id,
            "parent_name": parent_name,
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
            "message": "Department added successfully",
            "data": {
                "id": result.lastrowid,
                "dept_name": request.dept_name,
                "dept_code": request.dept_code,
                "parent_id": request.parent_id,
                "parent_name": parent_name,
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


# 修改部门
@router.put("/departments/update/{id}")
async def departments_update(
    id: int,
    request: DepartmentUpdateRequest,
    updater_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    try:
        from datetime import datetime
        current_time = datetime.now()

        if request.dept_name:
            check_result = db.execute(
                text("SELECT COUNT(*) as count FROM departments WHERE dept_name = :dept_name AND id != :id"),
                {"dept_name": request.dept_name, "id": id}
            )
            count = check_result.fetchone().count
            if count > 0:
                return {
                    "status": "error",
                    "message": f"Department name '{request.dept_name}' already exists",
                    "data": None
                }

        if request.dept_code:
            check_result = db.execute(
                text("SELECT COUNT(*) as count FROM departments WHERE dept_code = :dept_code AND id != :id"),
                {"dept_code": request.dept_code, "id": id}
            )
            count = check_result.fetchone().count
            if count > 0:
                return {
                    "status": "error",
                    "message": f"Department code '{request.dept_code}' already exists",
                    "data": None
                }

        parent_name = None
        if request.parent_id is not None:
            parent_result = db.execute(
                text("SELECT dept_name FROM departments WHERE id = :parent_id LIMIT 1"),
                {"parent_id": request.parent_id}
            )
            parent_record = parent_result.fetchone()
            if parent_record:
                parent_name = parent_record.dept_name
            else:
                return {
                    "status": "error",
                    "message": f"Parent department with id {request.parent_id} not found",
                    "data": None
                }

        update_data = {
            "dept_name": request.dept_name,
            "dept_code": request.dept_code,
            "parent_id": request.parent_id,
            "parent_name": parent_name,
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
        sql = f"UPDATE departments SET {set_str} WHERE id = :id"

        result = db.execute(text(sql), values)
        db.commit()

        if result.rowcount == 0:
            return {
                "status": "ok",
                "message": "Department not found",
                "data": None
            }

        updated_at_str = current_time.strftime("%Y-%m-%d %H:%M:%S")

        select_result = db.execute(
            text("""
                SELECT id, dept_name, dept_code, parent_id, parent_name, creator_id, updater_id,
                       DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at
                FROM departments WHERE id = :id LIMIT 1
            """),
            {"id": id}
        )
        record = select_result.fetchone()

        return {
            "status": "ok",
            "message": "Department updated successfully",
            "data": {
                "id": record.id,
                "dept_name": record.dept_name,
                "dept_code": record.dept_code,
                "parent_id": record.parent_id,
                "parent_name": record.parent_name,
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


# 删除部门
@router.delete("/departments/delete/{id}")
async def departments_delete(
    id: int,
    db: Session = Depends(get_db)
):
    try:
        check_result = db.execute(
            text("SELECT COUNT(*) as count FROM departments WHERE parent_id = :id"),
            {"id": id}
        )
        count = check_result.fetchone().count

        if count > 0:
            return {
                "status": "error",
                "message": f"Cannot delete department: {count} sub-department(s) exist",
                "data": None
            }

        result = db.execute(text("DELETE FROM departments WHERE id = :id"), {"id": id})
        db.commit()

        if result.rowcount == 0:
            return {
                "status": "ok",
                "message": "Department not found",
                "data": None
            }

        return {
            "status": "ok",
            "message": "Department deleted successfully",
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
