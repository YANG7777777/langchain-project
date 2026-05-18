from fastapi import APIRouter, Depends
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.dependencies.database import get_db
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(tags=["Permission"])


class MenuAddRequest(BaseModel):
    menu_name: str = Field(..., min_length=1, max_length=100, description="菜单名称")
    menu_code: Optional[str] = Field(None, max_length=100, description="菜单代码")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    menu_path: Optional[str] = Field(None, max_length=255, description="菜单路径")
    menu_icon: Optional[str] = Field(None, max_length=100, description="菜单图标")
    sort_order: Optional[int] = Field(0, description="排序")


class MenuUpdateRequest(BaseModel):
    menu_name: Optional[str] = Field(None, min_length=1, max_length=100, description="菜单名称")
    menu_code: Optional[str] = Field(None, max_length=100, description="菜单代码")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    menu_path: Optional[str] = Field(None, max_length=255, description="菜单路径")
    menu_icon: Optional[str] = Field(None, max_length=100, description="菜单图标")
    sort_order: Optional[int] = Field(None, description="排序")


class MenuPermissionRequest(BaseModel):
    role_id: int = Field(..., description="角色ID")
    menu_ids: List[int] = Field(..., description="菜单ID列表")


@router.get("/menus/all")
async def menus_all(
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    try:
        # 先获取所有菜单
        result = db.execute(
            text("""
                SELECT id, menu_name, menu_code, parent_id, menu_path, menu_icon,
                       sort_order, creator_id, updater_id,
                       DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                       DATE_FORMAT(updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
                FROM menus
                ORDER BY sort_order ASC, id ASC
            """)
        )
        all_records = result.fetchall()

        # 转换为字典格式
        menu_dict = {}
        for record in all_records:
            menu = {
                "id": record.id,
                "menu_name": record.menu_name,
                "menu_code": record.menu_code,
                "parent_id": record.parent_id,
                "menu_path": record.menu_path,
                "menu_icon": record.menu_icon,
                "sort_order": record.sort_order,
                "creator_id": record.creator_id,
                "updater_id": record.updater_id,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
                "children": []
            }
            menu_dict[record.id] = menu

        # 构建树形结构
        tree = []
        for menu_id, menu in menu_dict.items():
            parent_id_val = menu["parent_id"]
            if parent_id_val is None or parent_id_val == 0:
                tree.append(menu)
            else:
                if parent_id_val in menu_dict:
                    menu_dict[parent_id_val]["children"].append(menu)

        # 如果指定了 parent_id，则只返回该父节点的子菜单
        if parent_id is not None:
            filtered = []
            for menu in tree:
                if menu["id"] == parent_id:
                    filtered = menu["children"]
                    break
            return {
                "status": "ok",
                "message": "Menus retrieved successfully",
                "data": filtered
            }

        return {
            "status": "ok",
            "message": "All menus retrieved successfully",
            "data": tree
        }

    except SQLAlchemyError as e:
        return {
            "status": "error",
            "message": f"Database query failed: {str(e)}",
            "data": None
        }


@router.post("/menus/add")
async def menus_add(
    request: MenuAddRequest,
    creator_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    try:
        now = datetime.now()
        id_result = db.execute(text("SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM menus"))
        next_id = id_result.fetchone().next_id

        db.execute(
            text("""
                INSERT INTO menus (id, menu_name, menu_code, parent_id, menu_path, menu_icon, sort_order, creator_id, updater_id, created_at, updated_at)
                VALUES (:id, :menu_name, :menu_code, :parent_id, :menu_path, :menu_icon, :sort_order, :creator_id, :updater_id, :created_at, :updated_at)
            """),
            {
                "id": next_id,
                "menu_name": request.menu_name,
                "menu_code": request.menu_code,
                "parent_id": request.parent_id,
                "menu_path": request.menu_path,
                "menu_icon": request.menu_icon,
                "sort_order": request.sort_order,
                "creator_id": creator_id,
                "updater_id": creator_id,
                "created_at": now,
                "updated_at": now
            }
        )
        db.commit()

        return {
            "status": "ok",
            "message": "Menu added successfully",
            "data": {"id": next_id}
        }

    except SQLAlchemyError as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Database operation failed: {str(e)}",
            "data": None
        }


@router.put("/menus/update/{id}")
async def menus_update(
    id: int,
    request: MenuUpdateRequest,
    updater_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    try:
        now = datetime.now()
        check_result = db.execute(text("SELECT COUNT(*) as count FROM menus WHERE id = :id"), {"id": id})
        if check_result.fetchone().count == 0:
            return {
                "status": "error",
                "message": "Menu not found",
                "data": None
            }

        update_data = {
            "menu_name": request.menu_name,
            "menu_code": request.menu_code,
            "parent_id": request.parent_id,
            "menu_path": request.menu_path,
            "menu_icon": request.menu_icon,
            "sort_order": request.sort_order,
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
        sql = f"UPDATE menus SET {set_str} WHERE id = :id"

        db.execute(text(sql), values)
        db.commit()

        return {
            "status": "ok",
            "message": "Menu updated successfully",
            "data": {"id": id}
        }

    except SQLAlchemyError as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Database operation failed: {str(e)}",
            "data": None
        }


@router.delete("/menus/delete/{id}")
async def menus_delete(
    id: int,
    db: Session = Depends(get_db)
):
    try:
        db.execute(text("DELETE FROM role_menus WHERE menu_id = :id"), {"id": id})
        result = db.execute(text("DELETE FROM menus WHERE id = :id"), {"id": id})
        db.commit()

        if result.rowcount == 0:
            return {
                "status": "error",
                "message": "Menu not found",
                "data": None
            }

        return {
            "status": "ok",
            "message": "Menu deleted successfully",
            "data": {"id": id}
        }

    except SQLAlchemyError as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Database operation failed: {str(e)}",
            "data": None
        }


@router.get("/menus/by-role/{role_id}")
async def get_menus_by_role(
    role_id: int,
    db: Session = Depends(get_db)
):
    try:
        # 获取该角色的所有菜单ID
        role_menus_result = db.execute(
            text("SELECT menu_id FROM role_menus WHERE role_id = :role_id"),
            {"role_id": role_id}
        )
        menu_ids = [row.menu_id for row in role_menus_result.fetchall()]

        if not menu_ids:
            return {
                "status": "ok",
                "message": "Menus retrieved successfully",
                "data": []
            }

        # 获取所有菜单（用于构建完整树）
        result = db.execute(
            text("""
                SELECT id, menu_name, menu_code, parent_id, menu_path, menu_icon,
                       sort_order, creator_id, updater_id,
                       DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                       DATE_FORMAT(updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
                FROM menus
                ORDER BY sort_order ASC, id ASC
            """)
        )
        all_records = result.fetchall()

        # 转换为字典格式
        menu_dict = {}
        for record in all_records:
            menu = {
                "id": record.id,
                "menu_name": record.menu_name,
                "menu_code": record.menu_code,
                "parent_id": record.parent_id,
                "menu_path": record.menu_path,
                "menu_icon": record.menu_icon,
                "sort_order": record.sort_order,
                "creator_id": record.creator_id,
                "updater_id": record.updater_id,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
                "children": []
            }
            menu_dict[record.id] = menu

        # 构建树形结构（只包含该角色有权限的菜单）
        tree = []
        for menu_id, menu in menu_dict.items():
            if menu_id in menu_ids:
                parent_id_val = menu["parent_id"]
                if parent_id_val is None or parent_id_val == 0:
                    tree.append(menu)
                else:
                    if parent_id_val in menu_dict:
                        menu_dict[parent_id_val]["children"].append(menu)

        return {
            "status": "ok",
            "message": "Menus retrieved successfully",
            "data": tree
        }

    except SQLAlchemyError as e:
        return {
            "status": "error",
            "message": f"Database query failed: {str(e)}",
            "data": None
        }


@router.post("/permissions/assign")
async def assign_permissions(
    request: MenuPermissionRequest,
    creator_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    try:
        now = datetime.now()
        db.execute(text("DELETE FROM role_menus WHERE role_id = :role_id"), {"role_id": request.role_id})

        for menu_id in request.menu_ids:
            id_result = db.execute(text("SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM role_menus"))
            next_id = id_result.fetchone().next_id
            db.execute(
                text("""
                    INSERT INTO role_menus (id, role_id, menu_id, creator_id, updater_id, created_at, updated_at)
                    VALUES (:id, :role_id, :menu_id, :creator_id, :updater_id, :created_at, :updated_at)
                """),
                {
                    "id": next_id,
                    "role_id": request.role_id,
                    "menu_id": menu_id,
                    "creator_id": creator_id,
                    "updater_id": creator_id,
                    "created_at": now,
                    "updated_at": now
                }
            )

        db.commit()

        return {
            "status": "ok",
            "message": "Permissions assigned successfully",
            "data": {"role_id": request.role_id, "menu_count": len(request.menu_ids)}
        }

    except SQLAlchemyError as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Database operation failed: {str(e)}",
            "data": None
        }


@router.get("/permissions/by-role/{role_id}")
async def get_permissions_by_role(
    role_id: int,
    db: Session = Depends(get_db)
):
    try:
        result = db.execute(
            text("""
                SELECT rm.id, rm.role_id, rm.menu_id, m.menu_name, m.menu_code,
                       DATE_FORMAT(rm.created_at, '%Y-%m-%d %H:%i:%s') as created_at
                FROM role_menus rm
                INNER JOIN menus m ON rm.menu_id = m.id
                WHERE rm.role_id = :role_id
                ORDER BY rm.id ASC
            """),
            {"role_id": role_id}
        )
        records = result.fetchall()

        permission_list = []
        for record in records:
            permission_list.append({
                "id": record.id,
                "role_id": record.role_id,
                "menu_id": record.menu_id,
                "menu_name": record.menu_name,
                "menu_code": record.menu_code,
                "created_at": record.created_at
            })

        return {
            "status": "ok",
            "message": "Permissions retrieved successfully",
            "data": permission_list
        }

    except SQLAlchemyError as e:
        return {
            "status": "error",
            "message": f"Database query failed: {str(e)}",
            "data": None
        }


@router.get("/menus/current")
async def get_current_user_menus(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """根据用户ID获取菜单。如果没有提供user_id，则返回所有菜单。"""
    try:
        if user_id is None:
            # 如果没有用户ID，返回所有菜单
            # 先获取所有菜单
            result = db.execute(
                text("""
                    SELECT id, menu_name, menu_code, parent_id, menu_path, menu_icon,
                           sort_order, creator_id, updater_id,
                           DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') as created_at,
                           DATE_FORMAT(updated_at, '%Y-%m-%d %H:%i:%s') as updated_at
                    FROM menus
                    ORDER BY sort_order ASC, id ASC
                """)
            )
            all_records = result.fetchall()

            # 转换为字典格式
            menu_dict = {}
            for record in all_records:
                menu = {
                    "id": record.id,
                    "menu_name": record.menu_name,
                    "menu_code": record.menu_code,
                    "parent_id": record.parent_id,
                    "menu_path": record.menu_path,
                    "menu_icon": record.menu_icon,
                    "sort_order": record.sort_order,
                    "creator_id": record.creator_id,
                    "updater_id": record.updater_id,
                    "created_at": record.created_at,
                    "updated_at": record.updated_at,
                    "children": []
                }
                menu_dict[record.id] = menu

            # 构建树形结构
            tree = []
            for menu_id, menu in menu_dict.items():
                parent_id_val = menu["parent_id"]
                if parent_id_val is None or parent_id_val == 0:
                    tree.append(menu)
                else:
                    if parent_id_val in menu_dict:
                        menu_dict[parent_id_val]["children"].append(menu)

            return {
                "status": "ok",
                "message": "All menus retrieved successfully",
                "data": tree
            }

        # 获取用户的 role_code
        user_result = db.execute(
            text("SELECT role FROM users WHERE id = :user_id LIMIT 1"),
            {"user_id": user_id}
        )
        user_record = user_result.fetchone()

        if user_record is None or user_record.role is None:
            return {
                "status": "ok",
                "message": "Menus retrieved successfully",
                "data": []
            }

        role_code = user_record.role

        # 根据 role_code 获取 role_id
        role_result = db.execute(
            text("SELECT id FROM roles WHERE role_code = :role_code LIMIT 1"),
            {"role_code": role_code}
        )
        role_record = role_result.fetchone()

        if role_record is None:
            return {
                "status": "ok",
                "message": "Menus retrieved successfully",
                "data": []
            }

        role_id = role_record.id

        # 获取该角色的菜单
        return await get_menus_by_role(role_id, db)

    except SQLAlchemyError as e:
        return {
            "status": "error",
            "message": f"Database query failed: {str(e)}",
            "data": None
        }