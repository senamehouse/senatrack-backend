from fastapi import APIRouter, HTTPException, Depends
from app.services.sync import SyncService
from app.core.dependencies import get_current_active_user
from app.schemas.user import User

router = APIRouter( prefix="/sync", tags=["Sync"])
sync_service = SyncService()

@router.get("/status")
async def get_sync_status(current_user: User = Depends(get_current_active_user)):
    """Get current sync status (requires authentication)"""
    return await sync_service.get_sync_status()

@router.post("/to-server")
async def sync_to_server(current_user: User = Depends(get_current_active_user)):
    """Sync local changes to server database (requires authentication)"""
    result = await sync_service.sync_to_server()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.post("/from-server")
async def sync_from_server(current_user: User = Depends(get_current_active_user)):
    """Sync server data to local database (requires authentication)"""
    result = await sync_service.sync_from_server()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.post("/bidirectional")
async def bidirectional_sync(current_user: User = Depends(get_current_active_user)):
    """Perform bidirectional sync between local and server databases (requires authentication)"""
    result = await sync_service.bidirectional_sync()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@router.post("/force")
async def force_sync(current_user: User = Depends(get_current_active_user)):
    """Force sync all data (overwrites local with server data) (requires authentication)"""
    result = await sync_service.force_sync_all()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result
