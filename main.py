from fastapi import FastAPI
from app.dependencies.middleware import add_cors_middleware


def create_app() -> FastAPI:
    # 初始化加密模块
    from app.utils.crypto import init_crypto
    init_crypto()

    _app = FastAPI(
        description="LangChain RAG API with FastAPI",
        version="0.1.0",
        title="LangChain RAG API",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 添加中间件
    add_cors_middleware(_app)

    # 注册路由（延迟导入以支持热重载）
    from app.routes import blogs, ai, user, login, roles, departments, userInfo, permission
    from app.routes.clock_records import router as clock_records_router
    from app.routes.ask_leave import router as ask_leave_router
    _app.include_router(blogs.router)
    _app.include_router(ai.router)
    _app.include_router(user.router)
    _app.include_router(login.router)
    _app.include_router(roles.router)
    _app.include_router(departments.router)
    _app.include_router(userInfo.router)
    _app.include_router(permission.router)
    _app.include_router(clock_records_router)
    _app.include_router(ask_leave_router)
    return _app


# 模块级别创建应用，支持热重载
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    # 使用字符串导入方式支持热重载
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)  # http://localhost:8000/docs#/