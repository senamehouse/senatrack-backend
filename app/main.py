# Create a FastAPI app instance
from fastapi import FastAPI, Request, HTTPException, status
from fastapi import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from app.core.settings import settings
from app.routes.user_route import router as user_router
from app.routes.sync_route import router as sync_router
from app.routes.auth_route import router as auth_router
from app.routes.product_route import router as product_router
from app.routes.supplier_route import router as supplier_router
from app.routes.client_route import router as client_router
from app.routes.service_route import router as service_router
from app.routes.stock_movement_route import router as stock_movement_router
from app.routes.sales_route import router as sales_router
from app.routes.purchase_order_route import router as purchase_order_router
from app.routes.reception_route import router as reception_router
from app.routes.employee_route import router as employee_router
from app.routes.leave_route import router as leave_router
from app.routes.payroll_route import router as payroll_router
from app.routes.performance_route import router as performance_router
from app.routes.utils_route import router as utils_router
from app.routes.activity_route import router as activity_router
from app.routes.company_route import router as company_router
from app.routes.proforma_route import router as proforma_router
from app.routes.invitation_route import router as invitation_router
from app.routes.activation_key_route import router as activation_key_router
from app.routes.file_route import router as file_router
from app.routes.user_role_route import router as user_role_router
from app.routes.company_role_route import router as company_role_router
from app.routes.migration_route import router as migration_router
from app.routes.dashboard_route import router as dashboard_router

from app.core.database import init_database, get_database_info
# Import all models to ensure they're registered with Base.metadata
import app.models  # This ensures all models are loaded and registered with Base.metadata

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
)

# Configure CORS
# When credentials are included, we cannot use wildcard "*" for origins
# We must specify the exact origins
allowed_origins = [
    "https://gestion.senatrack.app",
    "http://localhost:4000",  # Local development
    "http://localhost:4001",  # Alternative local port
]

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_database()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/database-info")
async def get_database_info_endpoint():
    """Get information about current database configuration"""
    return get_database_info()

# Include all routers directly without /api prefix
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(sync_router)
app.include_router(product_router)
app.include_router(supplier_router)
app.include_router(client_router)
app.include_router(service_router)
app.include_router(stock_movement_router)
app.include_router(sales_router)
app.include_router(purchase_order_router)
app.include_router(reception_router)
app.include_router(employee_router)
app.include_router(leave_router)
app.include_router(payroll_router)
app.include_router(performance_router)
app.include_router(utils_router)
app.include_router(activity_router)
app.include_router(company_router)
app.include_router(proforma_router)
app.include_router(invitation_router)
app.include_router(activation_key_router)
app.include_router(file_router)
app.include_router(user_role_router)
app.include_router(company_role_router)
app.include_router(migration_router)
app.include_router(dashboard_router)