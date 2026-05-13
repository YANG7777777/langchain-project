from fastapi import APIRouter, Depends
from typing import Optional
from pydantic import BaseModel, Field
from app.dependencies.database import get_db
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

router = APIRouter(tags=["Employees"])


class EmployeeResponse(BaseModel):
    status: str = Field("ok", description="状态")
    message: str = Field(..., description="状态描述")
    data: Optional[dict] = Field(None, description="员工数据")


class EmployeeListResponse(BaseModel):
    status: str = Field("ok", description="状态")
    message: str = Field(..., description="状态描述")
    data: Optional[dict] = Field(None, description="员工列表")


class EmployeeAddRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="姓名")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    birthday: Optional[str] = Field(None, description="生日，格式: YYYY-MM-DD")
    phone: Optional[str] = Field(None, max_length=20, description="手机")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    dept_code: Optional[str] = Field(None, max_length=50, description="部门编码")
    position: Optional[str] = Field(None, max_length=100, description="职位")
    hire_date: Optional[str] = Field(None, description="入职日期，格式: YYYY-MM-DD")
    confirmation_date: Optional[str] = Field(None, description="转正日期，格式: YYYY-MM-DD")
    status: Optional[int] = Field(None, ge=0, le=1, description="在职状态: 0-离职, 1-在职")
    salary: Optional[int] = Field(None, description="薪资")
    education: Optional[str] = Field(None, max_length=50, description="学历")


class EmployeeUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="姓名")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    birthday: Optional[str] = Field(None, description="生日，格式: YYYY-MM-DD")
    phone: Optional[str] = Field(None, max_length=20, description="手机")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    dept_code: Optional[str] = Field(None, max_length=50, description="部门编码")
    position: Optional[str] = Field(None, max_length=100, description="职位")
    hire_date: Optional[str] = Field(None, description="入职日期，格式: YYYY-MM-DD")
    confirmation_date: Optional[str] = Field(None, description="转正日期，格式: YYYY-MM-DD")
    resignation_date: Optional[str] = Field(None, description="离职日期，格式: YYYY-MM-DD")
    status: Optional[int] = Field(None, ge=0, le=1, description="在职状态: 0-离职, 1-在职")
    salary: Optional[int] = Field(None, description="薪资")
    education: Optional[str] = Field(None, max_length=50, description="学历")


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


def get_department_by_code(db: Session, dept_code: Optional[str]) -> Optional[str]:
    if not dept_code:
        return None
    result = db.execute(text("SELECT dept_name FROM departments WHERE dept_code = :dept_code LIMIT 1"), {"dept_code": dept_code})
    record = result.fetchone()
    return record.dept_name if record else None


# 获取所有员工（支持按 id 和 name 过滤）
@router.get("/employees/all")
async def employees_all(
    id: Optional[int] = None,
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        where_clauses = []
        params = {}

        if id is not None:
            where_clauses.append("e.id = :id")
            params["id"] = id

        if name is not None:
            where_clauses.append("e.name LIKE :name")
            params["name"] = f"%{name}%"

        where_sql = ""
        if where_clauses:
            where_sql = " WHERE " + " AND ".join(where_clauses)

        result = db.execute(
            text(f"""
                SELECT e.id, e.name, e.gender,
                       DATE_FORMAT(e.birthday, '%Y-%m-%d') as birthday,
                       e.phone, e.email, e.dept_code, 
                       COALESCE(d.dept_name, e.department_name) as department_name, 
                       e.position,
                       DATE_FORMAT(e.hire_date, '%Y-%m-%d') as hire_date,
                       DATE_FORMAT(e.confirmation_date, '%Y-%m-%d') as confirmation_date,
                       DATE_FORMAT(e.resignation_date, '%Y-%m-%d') as resignation_date,
                       e.status, e.salary, e.education,
                       e.creator_id, e.updater_id,
                       DATE_FORMAT(e.created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                       DATE_FORMAT(e.updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
                FROM employees e
                LEFT JOIN departments d ON e.dept_code = d.dept_code
                {where_sql}
                ORDER BY e.id ASC
            """),
            params
        )
        records = result.fetchall()

        employee_list = []
        for record in records:
            employee_list.append({
                "id": record.id,
                "name": record.name,
                "gender": record.gender,
                "birthday": record.birthday,
                "phone": record.phone,
                "email": record.email,
                "dept_code": record.dept_code,
                "department_name": record.department_name,
                "position": record.position,
                "hire_date": record.hire_date,
                "confirmation_date": record.confirmation_date,
                "resignation_date": record.resignation_date,
                "status": record.status,
                "salary": record.salary,
                "education": record.education,
                "creator_id": record.creator_id,
                "updater_id": record.updater_id,
                "created_at": record.created_at,
                "updated_at": record.updated_at
            })

        return {
            "status": "ok",
            "message": "All employees retrieved successfully",
            "data": {
                "list": employee_list,
                "total": len(employee_list)
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


# 获取员工详情
@router.get("/employees/detail/{id}")
async def employees_detail(
    id: int,
    db: Session = Depends(get_db)
):
    try:
        result = db.execute(
            text("""
                SELECT e.id, e.name, e.gender,
                       DATE_FORMAT(e.birthday, '%Y-%m-%d') as birthday,
                       e.phone, e.email, e.dept_code,
                       COALESCE(d.dept_name, e.department_name) as department_name,
                       e.position,
                       DATE_FORMAT(e.hire_date, '%Y-%m-%d') as hire_date,
                       DATE_FORMAT(e.confirmation_date, '%Y-%m-%d') as confirmation_date,
                       DATE_FORMAT(e.resignation_date, '%Y-%m-%d') as resignation_date,
                       e.status, e.salary, e.education,
                       e.creator_id, e.updater_id,
                       DATE_FORMAT(e.created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                       DATE_FORMAT(e.updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
                FROM employees e
                LEFT JOIN departments d ON e.dept_code = d.dept_code
                WHERE e.id = :id LIMIT 1
            """),
            {"id": id}
        )
        record = result.fetchone()

        if record is None:
            return {
                "status": "ok",
                "message": "Employee not found",
                "data": None
            }

        return {
            "status": "ok",
            "message": "Employee retrieved successfully",
            "data": {
                "id": record.id,
                "name": record.name,
                "gender": record.gender,
                "birthday": record.birthday,
                "phone": record.phone,
                "email": record.email,
                "dept_code": record.dept_code,
                "department_name": record.department_name,
                "position": record.position,
                "hire_date": record.hire_date,
                "confirmation_date": record.confirmation_date,
                "resignation_date": record.resignation_date,
                "status": record.status,
                "salary": record.salary,
                "education": record.education,
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


# 新增员工
@router.post("/employees/add")
async def employees_add(
    request: EmployeeAddRequest,
    creator_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    try:
        now = datetime.now()

        department_name = get_department_by_code(db, request.dept_code)
        if request.dept_code and not department_name:
            return {
                "status": "error",
                "message": f"Department with code {request.dept_code} not found",
                "data": None
            }

        updater_id = creator_id + 1 if creator_id is not None else None

        sql = text("""
            INSERT INTO employees (name, gender, birthday, phone, email, dept_code, department_name, position,
                                  hire_date, confirmation_date, status, salary, education,
                                  creator_id, updater_id, created_at, updated_at)
            VALUES (:name, :gender, :birthday, :phone, :email, :dept_code, :department_name, :position,
                    :hire_date, :confirmation_date, :status, :salary, :education,
                    :creator_id, :updater_id, :created_at, :updated_at)
        """)

        result = db.execute(sql, {
            "name": request.name,
            "gender": request.gender,
            "birthday": parse_date(request.birthday),
            "phone": request.phone,
            "email": request.email,
            "dept_code": request.dept_code,
            "department_name": department_name,
            "position": request.position,
            "hire_date": parse_date(request.hire_date),
            "confirmation_date": parse_date(request.confirmation_date),
            "status": request.status,
            "salary": request.salary,
            "education": request.education,
            "creator_id": creator_id,
            "updater_id": updater_id,
            "created_at": now,
            "updated_at": now
        })
        db.commit()

        new_id = result.lastrowid

        return {
            "status": "ok",
            "message": "Employee added successfully",
            "data": {
                "id": new_id,
                "name": request.name,
                "gender": request.gender,
                "birthday": request.birthday,
                "phone": request.phone,
                "email": request.email,
                "dept_code": request.dept_code,
                "department_name": department_name,
                "position": request.position,
                "hire_date": request.hire_date,
                "confirmation_date": request.confirmation_date,
                "status": request.status,
                "salary": request.salary,
                "education": request.education,
                "creator_id": creator_id,
                "updater_id": updater_id
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


# 修改员工
@router.put("/employees/update/{id}")
async def employees_update(
    id: int,
    request: EmployeeUpdateRequest,
    updater_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    try:
        now = datetime.now()

        check_result = db.execute(text("SELECT COUNT(*) as count FROM employees WHERE id = :id"), {"id": id})
        if check_result.fetchone().count == 0:
            return {
                "status": "ok",
                "message": "Employee not found",
                "data": None
            }

        department_name = None
        if request.dept_code is not None:
            department_name = get_department_by_code(db, request.dept_code)
            if request.dept_code and not department_name:
                return {
                    "status": "error",
                    "message": f"Department with code {request.dept_code} not found",
                    "data": None
                }

        update_data = {
            "name": request.name,
            "gender": request.gender,
            "birthday": parse_date(request.birthday) if request.birthday is not None else None,
            "phone": request.phone,
            "email": request.email,
            "dept_code": request.dept_code,
            "department_name": department_name,
            "position": request.position,
            "hire_date": parse_date(request.hire_date) if request.hire_date is not None else None,
            "confirmation_date": parse_date(request.confirmation_date) if request.confirmation_date is not None else None,
            "resignation_date": parse_date(request.resignation_date) if request.resignation_date is not None else None,
            "status": request.status,
            "salary": request.salary,
            "education": request.education,
            "updater_id": updater_id,
            "updated_at": now,
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
        sql = f"UPDATE employees SET {set_str} WHERE id = :id"

        db.execute(text(sql), values)
        db.commit()

        select_result = db.execute(
            text("""
                SELECT e.id, e.name, e.gender,
                       DATE_FORMAT(e.birthday, '%Y-%m-%d') as birthday,
                       e.phone, e.email, e.dept_code,
                       COALESCE(d.dept_name, e.department_name) as department_name,
                       e.position,
                       DATE_FORMAT(e.hire_date, '%Y-%m-%d') as hire_date,
                       DATE_FORMAT(e.confirmation_date, '%Y-%m-%d') as confirmation_date,
                       DATE_FORMAT(e.resignation_date, '%Y-%m-%d') as resignation_date,
                       e.status, e.salary, e.education,
                       e.creator_id, e.updater_id,
                       DATE_FORMAT(e.created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                       DATE_FORMAT(e.updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
                FROM employees e
                LEFT JOIN departments d ON e.dept_code = d.dept_code
                WHERE e.id = :id LIMIT 1
            """),
            {"id": id}
        )
        record = select_result.fetchone()

        return {
            "status": "ok",
            "message": "Employee updated successfully",
            "data": {
                "id": record.id,
                "name": record.name,
                "gender": record.gender,
                "birthday": record.birthday,
                "phone": record.phone,
                "email": record.email,
                "dept_code": record.dept_code,
                "department_name": record.department_name,
                "position": record.position,
                "hire_date": record.hire_date,
                "confirmation_date": record.confirmation_date,
                "resignation_date": record.resignation_date,
                "status": record.status,
                "salary": record.salary,
                "education": record.education,
                "creator_id": record.creator_id,
                "updater_id": record.updater_id,
                "created_at": record.created_at,
                "updated_at": record.updated_at
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


# 删除员工
@router.delete("/employees/delete/{id}")
async def employees_delete(
    id: int,
    db: Session = Depends(get_db)
):
    try:
        result = db.execute(text("DELETE FROM employees WHERE id = :id"), {"id": id})
        db.commit()

        if result.rowcount == 0:
            return {
                "status": "ok",
                "message": "Employee not found",
                "data": None
            }

        return {
            "status": "ok",
            "message": "Employee deleted successfully",
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
