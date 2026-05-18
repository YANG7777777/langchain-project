from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List
from app.dependencies.database import get_db
from sqlalchemy import text

router = APIRouter()


class ClockRecordRequest(BaseModel):
    employee_id: int = Field(..., description="员工ID")
    clock_in_time: Optional[str] = Field(None, description="上班打卡时间")
    clock_out_time: Optional[str] = Field(None, description="下班打卡时间")
    remark: Optional[str] = Field(None, description="备注")


class ClockRecordUpdateRequest(BaseModel):
    clock_in_time: Optional[str] = Field(None, description="上班打卡时间")
    clock_out_time: Optional[str] = Field(None, description="下班打卡时间")
    remark: Optional[str] = Field(None, description="备注")


@router.get("/clock-records/all")
async def get_all_clock_records(page: int = 1, pageSize: int = 10, employee_name: Optional[str] = None, employee_id: Optional[int] = None, db=Depends(get_db)):
    """获取所有打卡记录（分页+查询条件）"""
    try:
        offset = (page - 1) * pageSize
        
        # 构建查询条件
        where_clauses = []
        params = {}
        
        if employee_id is not None:
            where_clauses.append("cr.employee_id = :employee_id")
            params["employee_id"] = employee_id
        
        if employee_name:
            where_clauses.append("cr.employee_name LIKE :employee_name")
            params["employee_name"] = f"%{employee_name}%"
        
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # 计算总数
        count_query = text(f"SELECT COUNT(*) FROM clock_records cr{where_sql}")
        count_result = db.execute(count_query, params)
        total = count_result.scalar()
        
        # 查询列表
        query = text(f"""
            SELECT cr.id, cr.employee_id, cr.employee_name,
                   DATE_FORMAT(cr.clock_in_time, '%Y-%m-%d %H:%i:%s') as clock_in_time,
                   DATE_FORMAT(cr.clock_out_time, '%Y-%m-%d %H:%i:%s') as clock_out_time,
                   cr.date, cr.status, cr.remark,
                   DATE_FORMAT(cr.created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                   DATE_FORMAT(cr.updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
            FROM clock_records cr
            {where_sql}
            ORDER BY cr.date DESC, cr.created_at DESC
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
                "clock_in_time": row.clock_in_time,
                "clock_out_time": row.clock_out_time,
                "date": row.date,
                "status": row.status,
                "remark": row.remark,
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


@router.get("/clock-records/by-employee/{employee_id}")
async def get_clock_records_by_employee(employee_id: int, db=Depends(get_db)):
    """获取指定员工的打卡记录"""
    try:
        query = text("""
            SELECT cr.id, cr.employee_id, cr.employee_name,
                   DATE_FORMAT(cr.clock_in_time, '%Y-%m-%d %H:%i:%s') as clock_in_time,
                   DATE_FORMAT(cr.clock_out_time, '%Y-%m-%d %H:%i:%s') as clock_out_time,
                   cr.date, cr.status, cr.remark,
                   DATE_FORMAT(cr.created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                   DATE_FORMAT(cr.updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
            FROM clock_records cr
            WHERE cr.employee_id = :employee_id
            ORDER BY cr.date DESC, cr.created_at DESC
        """)
        result = db.execute(query, {"employee_id": employee_id})
        records = []
        for row in result:
            records.append({
                "id": row.id,
                "employee_id": row.employee_id,
                "employee_name": row.employee_name,
                "clock_in_time": row.clock_in_time,
                "clock_out_time": row.clock_out_time,
                "date": row.date,
                "status": row.status,
                "remark": row.remark,
                "created_at": row.created_at,
                "updated_at": row.updated_at
            })
        return {"status": "ok", "data": records}
    except Exception as e:
        return {"status": "error", "message": f"Database query failed: {str(e)}"}


@router.get("/clock-records/today/{employee_id}")
async def get_today_clock_record(employee_id: int, db=Depends(get_db)):
    """获取员工今日打卡记录"""
    try:
        today = date.today().strftime('%Y-%m-%d')
        query = text("""
            SELECT cr.id, cr.employee_id, cr.employee_name,
                   DATE_FORMAT(cr.clock_in_time, '%Y-%m-%d %H:%i:%s') as clock_in_time,
                   DATE_FORMAT(cr.clock_out_time, '%Y-%m-%d %H:%i:%s') as clock_out_time,
                   cr.date, cr.status, cr.remark,
                   DATE_FORMAT(cr.created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                   DATE_FORMAT(cr.updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
            FROM clock_records cr
            WHERE cr.employee_id = :employee_id AND cr.date = :date
        """)
        result = db.execute(query, {"employee_id": employee_id, "date": today})
        row = result.first()
        if row:
            return {
                "status": "ok",
                "data": {
                    "id": row.id,
                    "employee_id": row.employee_id,
                    "employee_name": row.employee_name,
                    "clock_in_time": row.clock_in_time,
                    "clock_out_time": row.clock_out_time,
                    "date": row.date,
                    "status": row.status,
                    "remark": row.remark,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at
                }
            }
        return {"status": "ok", "data": None}
    except Exception as e:
        return {"status": "error", "message": f"Database query failed: {str(e)}"}


@router.post("/clock-records/add")
async def add_clock_record(request: ClockRecordRequest, db=Depends(get_db)):
    """新增打卡记录"""
    try:
        today = date.today().strftime('%Y-%m-%d')
        
        query = text("SELECT name FROM employees WHERE id = :employee_id")
        result = db.execute(query, {"employee_id": request.employee_id})
        employee = result.first()
        if not employee:
            return {"status": "error", "message": "员工不存在"}
        
        employee_name = employee.name
        
        check_query = text("""
            SELECT id FROM clock_records 
            WHERE employee_id = :employee_id AND date = :date
        """)
        exists = db.execute(check_query, {"employee_id": request.employee_id, "date": today}).first()
        
        if exists:
            return {"status": "error", "message": "今日已打卡"}
        
        insert_query = text("""
            INSERT INTO clock_records (employee_id, employee_name, clock_in_time, clock_out_time, date, status, remark)
            VALUES (:employee_id, :employee_name, :clock_in_time, :clock_out_time, :date, :status, :remark)
        """)
        db.execute(insert_query, {
            "employee_id": request.employee_id,
            "employee_name": employee_name,
            "clock_in_time": request.clock_in_time,
            "clock_out_time": request.clock_out_time,
            "date": today,
            "status": 1 if request.clock_in_time else 0,
            "remark": request.remark
        })
        db.commit()
        
        return {"status": "ok", "message": "打卡成功"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Database operation failed: {str(e)}"}


@router.put("/clock-records/update/{record_id}")
async def update_clock_record(record_id: int, request: ClockRecordUpdateRequest, db=Depends(get_db)):
    """更新打卡记录"""
    try:
        update_fields = []
        params = {"id": record_id}
        
        if request.clock_in_time is not None:
            update_fields.append("clock_in_time = :clock_in_time")
            params["clock_in_time"] = request.clock_in_time
        
        if request.clock_out_time is not None:
            update_fields.append("clock_out_time = :clock_out_time")
            params["clock_out_time"] = request.clock_out_time
        
        if request.remark is not None:
            update_fields.append("remark = :remark")
            params["remark"] = request.remark
        
        if request.clock_in_time or request.clock_out_time:
            update_fields.append("status = 1")
        
        if not update_fields:
            return {"status": "error", "message": "没有需要更新的字段"}
        
        query = text(f"""
            UPDATE clock_records 
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE id = :id
        """)
        db.execute(query, params)
        db.commit()
        
        return {"status": "ok", "message": "更新成功"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Database operation failed: {str(e)}"}


@router.delete("/clock-records/delete/{record_id}")
async def delete_clock_record(record_id: int, db=Depends(get_db)):
    """删除打卡记录"""
    try:
        query = text("DELETE FROM clock_records WHERE id = :id")
        db.execute(query, {"id": record_id})
        db.commit()
        
        return {"status": "ok", "message": "删除成功"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Database operation failed: {str(e)}"}


@router.post("/clock-records/clock-in")
async def clock_in(employee_id: int, db=Depends(get_db)):
    """上班打卡"""
    try:
        today = date.today().strftime('%Y-%m-%d')
        now = datetime.now().strftime('%Y-%m-%d %H:%i:%s')
        
        query = text("SELECT name FROM employees WHERE id = :employee_id")
        result = db.execute(query, {"employee_id": employee_id})
        employee = result.first()
        if not employee:
            return {"status": "error", "message": "员工不存在"}
        
        employee_name = employee.name
        
        check_query = text("""
            SELECT id, clock_in_time FROM clock_records 
            WHERE employee_id = :employee_id AND date = :date
        """)
        exists = db.execute(check_query, {"employee_id": employee_id, "date": today}).first()
        
        if exists:
            if exists.clock_in_time:
                return {"status": "error", "message": "今日已上班打卡"}
            else:
                update_query = text("""
                    UPDATE clock_records 
                    SET clock_in_time = :clock_in_time, status = 1, updated_at = NOW()
                    WHERE id = :id
                """)
                db.execute(update_query, {"clock_in_time": now, "id": exists.id})
                db.commit()
                return {"status": "ok", "message": "打卡成功"}
        
        insert_query = text("""
            INSERT INTO clock_records (employee_id, employee_name, clock_in_time, date, status)
            VALUES (:employee_id, :employee_name, :clock_in_time, :date, 1)
        """)
        db.execute(insert_query, {
            "employee_id": employee_id,
            "employee_name": employee_name,
            "clock_in_time": now,
            "date": today
        })
        db.commit()
        
        return {"status": "ok", "message": "打卡成功"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Database operation failed: {str(e)}"}


@router.post("/clock-records/clock-out")
async def clock_out(employee_id: int, db=Depends(get_db)):
    """下班打卡"""
    try:
        today = date.today().strftime('%Y-%m-%d')
        now = datetime.now().strftime('%Y-%m-%d %H:%i:%s')
        
        check_query = text("""
            SELECT id, clock_out_time FROM clock_records 
            WHERE employee_id = :employee_id AND date = :date
        """)
        exists = db.execute(check_query, {"employee_id": employee_id, "date": today}).first()
        
        if not exists:
            return {"status": "error", "message": "今日未打卡，请先上班打卡"}
        
        if exists.clock_out_time:
            return {"status": "error", "message": "今日已下班打卡"}
        
        update_query = text("""
            UPDATE clock_records 
            SET clock_out_time = :clock_out_time, status = 2, updated_at = NOW()
            WHERE id = :id
        """)
        db.execute(update_query, {"clock_out_time": now, "id": exists.id})
        db.commit()
        
        return {"status": "ok", "message": "打卡成功"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Database operation failed: {str(e)}"}