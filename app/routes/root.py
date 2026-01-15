from fastapi import APIRouter, Depends
from app.dependencies.database import get_db
from sqlalchemy import text
from app.schemas.models import BlogsResponse, BlogsListResponse, BlogsAddRequest, BlogsUpdateRequest, BlogsDeleteRequest
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(tags=["Blogs"])

# 获取博客详情
@router.get("/blogs/detail/{id}", response_model=BlogsResponse)
async def blogs_check(
    id: int,
    db: Session = Depends(get_db)
):
    try:
        result = db.execute(text("SELECT * FROM blogs WHERE id = :id LIMIT 1"), {"id": id})
        record = result.fetchone()

        if record is None:
            return BlogsResponse(
                status="ok",
                message="Database connected, but no record found",
                data=None
            )
        
        return BlogsResponse(
            status="ok",
            message="Database connection successful",
            data={"id": record.id, "title": record.title, "content": record.content}
        )

    except SQLAlchemyError as e:
        return BlogsResponse(
            status="error",
            message=f"Database query failed: {str(e)}"
        )
    except Exception as e:
        return BlogsResponse(
            status="error",
            message=f"Unexpected error: {str(e)}"
        )


# 获取所有博客
@router.get("/blogs/all", response_model=BlogsListResponse)
async def blogs_all(
    db: Session = Depends(get_db)
):
    try:
        result = db.execute(text("SELECT id, title, content FROM blogs"))
        records = result.fetchall()

        if not records:
            return BlogsListResponse(
                status="ok",
                message="No blogs found",
                data=None
            )
        
        blog_list = [{"id": record.id, "title": record.title, "content": record.content} for record in records]
        
        return BlogsListResponse(
            status="ok",
            message="All blogs retrieved successfully",
            data=blog_list
        )

    except SQLAlchemyError as e:
        return BlogsListResponse(
            status="error",
            message=f"Database query failed: {str(e)}"
        )
    except Exception as e:
        return BlogsListResponse(
            status="error",
            message=f"Unexpected error: {str(e)}"
        )


# 新增博客
@router.post("/blogs/add", response_model=BlogsResponse)
async def blogs_add(
    request: BlogsAddRequest,
    db: Session = Depends(get_db)
):
    try:
        import time
        # current_time = int(time.time() * 1000)
        
        result = db.execute(
            text("INSERT INTO blogs (title, content, author) VALUES (:title, :content, :author)"),
            {"title": request.title, "content": request.content, "author": "admin"}
        )
        db.commit()
        
        return BlogsResponse(
            status="ok",
            message="Blog added successfully",
            data={"id": result.lastrowid, "title": request.title}
        )
    except SQLAlchemyError as e:
        db.rollback()
        return BlogsResponse(
            status="error",
            message=f"Database query failed: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        return BlogsResponse(
            status="error",
            message=f"Unexpected error: {str(e)}"
        )


# 修改博客
@router.put("/blogs/update/{id}", response_model=BlogsResponse)
async def blogs_update(
    id: int,
    request: BlogsUpdateRequest,
    db: Session = Depends(get_db)
):
    try:
        result = db.execute(
            text("UPDATE blogs SET title = :title, content = :content WHERE id = :id"),
            {"title": request.title, "content": request.content, "id": id}
        )
        db.commit()
        
        if result.rowcount == 0:
            return BlogsResponse(
                status="ok",
                message="Blog not found",
                data=None
            )
        
        return BlogsResponse(
            status="ok",
            message="Blog updated successfully",
            data={"id": id, "title": request.title}
        )
    except SQLAlchemyError as e:
        db.rollback()
        return BlogsResponse(
            status="error",
            message=f"Database query failed: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        return BlogsResponse(
            status="error",
            message=f"Unexpected error: {str(e)}"
        )


# 删除博客
@router.delete("/blogs/delete/{id}", response_model=BlogsResponse)
async def blogs_delete(
    id: int,
    db: Session = Depends(get_db)
):
    try:
        result = db.execute(text("DELETE FROM blogs WHERE id = :id"), {"id": id})
        db.commit()
        
        if result.rowcount == 0:
            return BlogsResponse(
                status="ok",
                message="Blog not found",
                data=None
            )
        
        return BlogsResponse(
            status="ok",
            message="Blog deleted successfully",
            data={"id": id}
        )
    except SQLAlchemyError as e:
        db.rollback()
        return BlogsResponse(
            status="error",
            message=f"Database query failed: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        return BlogsResponse(
            status="error",
            message=f"Unexpected error: {str(e)}"
        )
