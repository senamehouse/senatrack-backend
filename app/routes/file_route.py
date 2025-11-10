from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.services.file_service import FileService
from app.core.dependencies import get_current_user
from app.core.database import get_async_db
from app.schemas.user_schema import User

router = APIRouter(prefix="/files", tags=["Files"])
svc = FileService()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    entity_type: str = Form(...),
    entity_id: str = Form(...),
    field_name: str = Form(...),
    company_id: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await svc.save_file(
            file=file,
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            company_id=company_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_id}")
@router.head("/{file_id}")
async def get_file(
    file_id: str,
    session: AsyncSession = Depends(get_async_db)
):
    """Public endpoint for file retrieval - no authentication required for images"""
    rec = await svc.get_file(file_id)
    if not rec:
        raise HTTPException(status_code=404, detail="File not found")
    if rec.file_path and os.path.exists(rec.file_path):
        return FileResponse(rec.file_path, media_type=rec.content_type, filename=rec.original_filename)
    if rec.remote_url:
        # For S3 files, redirect to the S3 URL (works for <img> src)
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=rec.remote_url, status_code=302)
    raise HTTPException(status_code=404, detail="File not found")


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    ok = await svc.delete_file(file_id)
    if not ok:
        raise HTTPException(status_code=404, detail="File not found")
    return {"message": "File deleted"}


@router.post("/sync/offline-to-online")
async def sync_offline_to_online(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sync local files to S3 (offline → online).
    Use when switching from offline to online mode.
    """
    return await svc.sync_offline_to_online()


@router.post("/sync/online-to-offline")
async def sync_online_to_offline(
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download S3 files to local storage (online → offline).
    Use when switching from online to offline mode.
    """
    return await svc.sync_online_to_offline()


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_files(
    entity_type: str,
    entity_id: str,
    session: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """Get all active files for a specific entity"""
    return await svc.get_entity_files(entity_type, entity_id)


