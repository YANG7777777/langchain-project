from fastapi import FastAPI
from app.routes import root, ai
from app.dependencies.middleware import add_cors_middleware


def create_app() -> FastAPI:
    _app = FastAPI(
        description="LangChain RAG API with FastAPI",
        version="0.1.0",
        title="LangChain RAG API",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 添加中间件
    add_cors_middleware(_app)


    # 注册路由
    _app.include_router(root.router)
    _app.include_router(ai.router)

    return _app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)  # http://localhost:8000/docs#/