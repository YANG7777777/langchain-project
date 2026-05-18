from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List
from app.dependencies.database import get_db
from sqlalchemy import text

router = APIRouter()


class LeaveApplicationRequest(BaseModel):
    employee_id: int = Field(..., description="员工ID")
    leave_type: int = Field(..., description="请假类型: 0-事假, 1-病假, 2-年假, 3-婚假, 4-产假, 5-其他")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    reason: Optional[str] = Field(None, description="请假原因")


class LeaveApplicationUpdateRequest(BaseModel):
    status: Optional[int] = Field(None, description="状态: 0-待审批, 1-已批准, 2-已拒绝")


@router.get("/leave-applications/all")
async def get_all_leave_applications(page: int = 1, pageSize: int = 10, employee_name: Optional[str] = None, employee_id: Optional[int] = None, status: Optional[int] = None, db=Depends(get_db)):
    """获取所有请假申请（分页+查询条件）"""
    try:
        offset = (page - 1) * pageSize
        
        # 构建查询条件
        where_clauses = []
        params = {}
        
        if employee_id is not None:
            where_clauses.append("la.employee_id = :employee_id")
            params["employee_id"] = employee_id
        
        if employee_name:
            where_clauses.append("la.employee_name LIKE :employee_name")
            params["employee_name"] = f"%{employee_name}%"
        
        if status is not None:
            where_clauses.append("la.status = :status")
            params["status"] = status
        
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # 计算总数
        count_query = text(f"SELECT COUNT(*) FROM leave_applications la{where_sql}")
        count_result = db.execute(count_query, params)
        total = count_result.scalar()
        
        # 查询列表
        query = text(f"""
            SELECT la.id, la.employee_id, la.employee_name,
                   la.leave_type,
                   DATE_FORMAT(la.start_date, '%Y-%m-%d') as start_date,
                   DATE_FORMAT(la.end_date, '%Y-%m-%d') as end_date,
                   la.reason, la.status,
                   DATE_FORMAT(la.created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                   DATE_FORMAT(la.updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
            FROM leave_applications la
            {where_sql}
            ORDER BY la.created_at DESC
            LIMIT :offset, :pageSize
        """)
        params["offset"] = offset
        params["pageSize"] = pageSize
        result = db.execute(query, params)
        records = []
        for row in result:
            records.append({
                "id": row.id,
                "employee_id": row.employee_id,
                "employee_name": row.employee_name,
                "leave_type": row.leave_type,
                "start_date": row.start_date,
                "end_date": row.end_date,
                "reason": row.reason,
                "status": row.status,
                "created_at": row.created_at,
                "updated_at": row.updated_at
            })
        
        return {
            "status": "ok",
            "data": {
                "list": records,
                "page": page,
                "pageSize": pageSize,
                "total": total,
                "totalPages": (total + pageSize - 1) // pageSize
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Database query failed: {str(e)}"}


@router.get("/leave-applications/by-employee/{employee_id}")
async def get_leave_applications_by_employee(employee_id: int, db=Depends(get_db)):
    """获取指定员工的请假申请"""
    try:
        query = text("""
            SELECT la.id, la.employee_id, la.employee_name,
                   la.leave_type,
                   DATE_FORMAT(la.start_date, '%Y-%m-%d') as start_date,
                   DATE_FORMAT(la.end_date, '%Y-%m-%d') as end_date,
                   la.reason, la.status,
                   DATE_FORMAT(la.created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                   DATE_FORMAT(la.updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
            FROM leave_applications la
            WHERE la.employee_id = :employee_id
            ORDER BY la.created_at DESC
        """)
        result = db.execute(query, {"employee_id": employee_id})
        records = []
        for row in result:
            records.append({
                "id": row.id,
                "employee_id": row.employee_id,
                "employee_name": row.employee_name,
                "leave_type": row.leave_type,
                "start_date": row.start_date,
                "end_date": row.end_date,
                "reason": row.reason,
                "status": row.status,
                "created_at": row.created_at,
                "updated_at": row.updated_at
            })
        return {"status": "ok", "data": records}
    except Exception as e:
        return {"status": "error", "message": f"Database query failed: {str(e)}"}


@router.get("/leave-applications/{id}")
async def get_leave_application(id: int, db=Depends(get_db)):
    """获取单个请假申请"""
    try:
        query = text("""
            SELECT la.id, la.employee_id, la.employee_name,
                   la.leave_type,
                   DATE_FORMAT(la.start_date, '%Y-%m-%d') as start_date,
                   DATE_FORMAT(la.end_date, '%Y-%m-%d') as end_date,
                   la.reason, la.status,
                   DATE_FORMAT(la.created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                   DATE_FORMAT(la.updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
            FROM leave_applications la
            WHERE la.id = :id
        """)
        result = db.execute(query, {"id": id})
        row = result.first()
        if row:
            return {
                "status": "ok",
                "data": {
                    "id": row.id,
                    "employee_id": row.employee_id,
                    "employee_name": row.employee_name,
                    "leave_type": row.leave_type,
                    "start_date": row.start_date,
                    "end_date": row.end_date,
                    "reason": row.reason,
                    "status": row.status,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at
                }
            }
        return {"status": "error", "message": "Leave application not found", "data": None}
    except Exception as e:
        return {"status": "error", "message": f"Database query failed: {str(e)}"}


@router.post("/leave-applications/add")
async def add_leave_application(request: LeaveApplicationRequest, db=Depends(get_db)):
    """新增请假申请"""
    try:
        # 检查员工是否存在
        emp_query = text("SELECT name FROM employees WHERE id = :employee_id LIMIT 1")
        emp_result = db.execute(emp_query, {"employee_id": request.employee_id})
        employee = emp_result.first()
        if not employee:
            return {"status": "error", "message": "Employee not found", "data": None}
        
        employee_name = employee.name
        
        # 插入请假申请
        insert_query = text("""
            INSERT INTO leave_applications (employee_id, employee_name, leave_type, start_date, end_date, reason, status)
            VALUES (:employee_id, :employee_name, :leave_type, :start_date, :end_date, :reason, 0)
        """)
        db.execute(insert_query, {
            "employee_id": request.employee_id,
            "employee_name": employee_name,
            "leave_type": request.leave_type,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "reason": request.reason
        })
        db.commit()
        
        return {"status": "ok", "message": "Leave application submitted successfully", "data": None}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Database operation failed: {str(e)}"}


@router.put("/leave-applications/update/{id}")
async def update_leave_application(id: int, request: LeaveApplicationUpdateRequest, db=Depends(get_db)):
    """更新请假申请状态"""
    try:
        if request.status is None:
            return {"status": "error", "message": "No data to update", "data": None}
        
        update_query = text("""
            UPDATE leave_applications 
            SET status = :status, updated_at = NOW()
            WHERE id = :id
        """)
        db.execute(update_query, {"status": request.status, "id": id})
        db.commit()
        
        return {"status": "ok", "message": "Leave application updated successfully", "data": None}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Database operation failed: {str(e)}"}


@router.delete("/leave-applications/delete/{id}")
async def delete_leave_application(id: int, db=Depends(get_db)):
    """删除请假申请"""
    try:
        query = text("DELETE FROM leave_applications WHERE id = :id")
        db.execute(query, {"id": id})
        db.commit()
        
        return {"status": "ok", "message": "Leave application deleted successfully", "data": None}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Database operation failed: {str(e)}"}