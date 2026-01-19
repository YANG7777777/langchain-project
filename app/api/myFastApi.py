from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.blogs import router as root_router
from app.routes.ai import router as ai_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(root_router)
app.include_router(ai_router)

@app.get("/")
async def root():
    return {"message": "Hello World"}