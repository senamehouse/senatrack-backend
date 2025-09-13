# Create a FastAPI app instance
from fastapi import FastAPI
from app.core.settings import settings
from app.core.database import init_database
from app.routes.user import router as user_router
from app.routes.sync import router as sync_router
from app.routes.auth import router as auth_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_database()

@app.get("/")
async def read_root():
    return {"message": "Hello World - Senatrack Backend is running!"}

# Include routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(sync_router)