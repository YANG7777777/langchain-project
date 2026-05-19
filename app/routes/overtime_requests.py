from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.dependencies.database import get_db
from sqlalchemy import text
from sqlalchemy.orm import Session

router = APIRouter(tags=["Overtime Requests"])


class OvertimeRequestCreate(BaseModel):
    user_id: int = Field(..., description="用户ID")
    user_name: str = Field(..., description="用户名")
    overtime_date: str = Field(..., description="加班日期")
    start_time: str = Field(..., description="开始时间")
    end_time: str = Field(..., description="结束时间")
    reason: Optional[str] = Field(None, description="加班原因")


class OvertimeRequestUpdate(BaseModel):
    status: Optional[int] = Field(None, description="状态: 0-待审批, 1-已批准, 2-已拒绝")


@router.get("/overtime-requests/all")
async def get_all_overtime_requests(
    page: int = 1,
    pageSize: int = 10,
    user_name: Optional[str] = None,
    id: Optional[int] = None,
    status: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取所有加班申请（分页+查询条件）"""
    try:
        offset = (page - 1) * pageSize
        
        where_clauses = []
        params = {}
        
        if id is not None:
            where_clauses.append("otr.id = :id")
            params["id"] = id
        
        if user_name:
            where_clauses.append("otr.user_name LIKE :user_name")
            params["user_name"] = f"%{user_name}%"
        
        if status is not None:
            where_clauses.append("otr.status = :status")
            params["status"] = status
        
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        count_query = text(f"SELECT COUNT(*) FROM overtime_requests otr{where_sql}")
        count_result = db.execute(count_query, params)
        total = count_result.scalar()
        
        query = text(f"""
            SELECT otr.id, otr.user_id, otr.user_name,
                   otr.overtime_date,
                   otr.start_time,
                   otr.end_time,
                   otr.reason, otr.status,
                   DATE_FORMAT(otr.created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                   DATE_FORMAT(otr.updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
            FROM overtime_requests otr
            {where_sql}
            ORDER BY otr.created_at DESC
            LIMIT :offset, :pageSize
        """)
        params["offset"] = offset
        params["pageSize"] = pageSize
        result = db.execute(query, params)
        records = []
        for row in result:
            records.append({
                "id": row.id,
                "user_id": row.user_id,
                "user_name": row.user_name,
                "overtime_date": row.overtime_date,
                "start_time": row.start_time,
                "end_time": row.end_time,
                "reason": row.reason,
                "status": row.status,
                "created_at": row.created_at,
                "updated_at": row.updated_at
            })
        
        return {
            "status": "ok",
            "data": {
                "list": records,
                "total": total
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Database query failed: {str(e)}"}


@router.get("/overtime-requests/{id}")
async def get_overtime_request(id: int, db: Session = Depends(get_db)):
    """获取单个加班申请"""
    try:
        query = text("""
            SELECT otr.id, otr.user_id, otr.user_name,
                   otr.overtime_date,
                   otr.start_time,
                   otr.end_time,
                   otr.reason, otr.status,
                   DATE_FORMAT(otr.created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                   DATE_FORMAT(otr.updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
            FROM overtime_requests otr
            WHERE otr.id = :id
        """)
        result = db.execute(query, {"id": id})
        row = result.first()
        if row:
            return {
                "status": "ok",
                "data": {
                    "id": row.id,
                    "user_id": row.user_id,
                    "user_name": row.user_name,
                    "overtime_date": row.overtime_date,
                    "start_time": row.start_time,
                    "end_time": row.end_time,
                    "reason": row.reason,
                    "status": row.status,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at
                }
            }
        return {"status": "error", "message": "Overtime request not found", "data": None}
    except Exception as e:
        return {"status": "error", "message": f"Database query failed: {str(e)}"}


@router.post("/overtime-requests/add")
async def add_overtime_request(request: OvertimeRequestCreate, db: Session = Depends(get_db)):
    """新增加班申请"""
    try:
        insert_query = text("""
            INSERT INTO overtime_requests (user_id, user_name, overtime_date, start_time, end_time, reason, status, created_at, updated_at)
            VALUES (:user_id, :user_name, :overtime_date, :start_time, :end_time, :reason, 0, NOW(), NOW())
        """)
        db.execute(insert_query, {
            "user_id": request.user_id,
            "user_name": request.user_name,
            "overtime_date": request.overtime_date,
            "start_time": request.start_time,
            "end_time": request.end_time,
            "reason": request.reason
        })
        db.commit()
        
        return {"status": "ok", "message": "Overtime request submitted successfully", "data": None}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Database operation failed: {str(e)}"}


@router.put("/overtime-requests/update/{id}")
async def update_overtime_request(id: int, request: OvertimeRequestUpdate, db: Session = Depends(get_db)):
    """更新加班申请状态"""
    try:
        if request.status is None:
            return {"status": "error", "message": "No data to update", "data": None}
        
        update_query = text("""
            UPDATE overtime_requests 
            SET status = :status,
                updated_at = NOW()
            WHERE id = :id
        """)
        db.execute(update_query, {
            "status": request.status,
            "id": id
        })
        db.commit()
        
        return {"status": "ok", "message": "Overtime request updated successfully", "data": None}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Database operation failed: {str(e)}"}


@router.delete("/overtime-requests/delete/{id}")
async def delete_overtime_request(id: int, db: Session = Depends(get_db)):
    """删除加班申请"""
    try:
        query = text("DELETE FROM overtime_requests WHERE id = :id")
        db.execute(query, {"id": id})
        db.commit()
        
        return {"status": "ok", "message": "Overtime request deleted successfully", "data": None}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Database operation failed: {str(e)}"}