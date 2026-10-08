from fastapi import APIRouter, Depends
from app.core.dependencies import require_admin_access
from app.services.sync_service import SyncService

router = APIRouter(prefix="/api/sync", tags=["Sync"], dependencies=[Depends(require_admin_access)])
svc = SyncService()

@router.post("/to-online")
async def sync_to_online():
    return await svc.sync_to_server()

@router.post("/from-online")
async def sync_from_online():
    return await svc.sync_from_server()

@router.post("/bidirectional")
async def sync_bidirectional():
    return await svc.bidirectional_sync()

@router.get("/status")
async def sync_status():
    return await svc.get_sync_status()
