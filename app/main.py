# Create a FastAPI app instance
from fastapi import FastAPI
from core.settings import settings
from routes.user import router as user_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
)

@app.get("/")
def read_root():
    return {"message": "Hello World"}

app.include_router(user_router)