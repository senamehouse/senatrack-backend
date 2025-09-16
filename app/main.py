# Create a FastAPI app instance
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.settings import settings
from app.core.database import init_database
from app.routes.user import router as user_router
from app.routes.sync import router as sync_router
from app.routes.auth import router as auth_router
from app.routes.product import router as product_router
from app.routes.activity import router as activity_router
from app.routes.business import router as business_router
from app.routes.company import router as company_router
from app.routes.proforma import router as proforma_router
from app.routes.invitation import router as invitation_router
from app.routes.activation_key import router as activation_key_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
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
app.include_router(product_router)
app.include_router(activity_router)
app.include_router(business_router)
app.include_router(company_router)
app.include_router(proforma_router)
app.include_router(invitation_router)
app.include_router(activation_key_router)