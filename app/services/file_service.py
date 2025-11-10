import os
import mimetypes
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import aiofiles

from fastapi import HTTPException, UploadFile
from sqlalchemy import select, update

from app.core.settings import settings
from app.core.database import get_db_session
from app.models.file_model import FileRecord
from app.services.upload_service import UploadService


class FileService:
    """File management with multipart handling, deduplication, cleanup, and hybrid storage"""

    def __init__(self):
        self.upload_service = UploadService()
        self.local_files_path = Path(settings.LOCAL_FILES_PATH)
        self.local_files_path.mkdir(exist_ok=True)

    async def _validate_file(self, file: UploadFile):
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        content = await file.read()
        await file.seek(0)
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        if file.content_type not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(status_code=400, detail="File type not allowed")

    def _generate_hash(self, content: bytes, entity_id: str, field_name: str) -> str:
        h = hashlib.md5()
        h.update(content)
        h.update(entity_id.encode())
        h.update(field_name.encode())
        return h.hexdigest()

    def _unique_filename(self, original: str, file_hash: str) -> str:
        ext = Path(original).suffix or mimetypes.guess_extension(mimetypes.guess_type(original)[0] or "") or ""
        return f"{file_hash}{ext}"

    def _entity_storage_dir(self, entity_type: str, entity_id: str, field_name: str) -> Path:
        return self.local_files_path / entity_type / entity_id / field_name

    async def save_file(
        self,
        file: UploadFile,
        entity_type: str,
        entity_id: str,
        field_name: str,
        company_id: Optional[str] = None,
        replace_existing: bool = True,
    ) -> Dict[str, Any]:
        """
        Save file based on DATABASE_MODE:
        - online: Direct upload to S3
        - offline: Save to local filesystem only
        """
        await self._validate_file(file)
        content = await file.read()
        file_hash = self._generate_hash(content, entity_id, field_name)

        # try dedupe by hash
        session = get_db_session()
        existing = await session.execute(
            select(FileRecord).where(FileRecord.file_hash == file_hash, FileRecord.is_active == True).limit(1)
        )
        existing_file = existing.scalar_one_or_none()

        if existing_file:
            # Link to existing file, optionally disable previous links for same field
            if replace_existing:
                await self._deactivate_existing(entity_type, entity_id, field_name)
            return await self._clone_link(existing_file, entity_type, entity_id, field_name, company_id)

        if replace_existing:
            await self._deactivate_existing(entity_type, entity_id, field_name)

        # Determine storage based on DATABASE_MODE
        mode = (settings.DATABASE_MODE or "offline").lower()
        filename = self._unique_filename(file.filename, file_hash)
        file_path = None
        remote_url = None
        sync_status = "not_applicable"
        storage_mode = "local"

        if mode == "online":
            # Online mode: Upload directly to S3
            s3_path = f"{entity_type}/{entity_id}/{field_name}/{filename}"
            remote_url = await self.upload_service.upload_to_s3(
                file_content=content,
                destination_path=s3_path,
                content_type=file.content_type or "application/octet-stream",
            )
            sync_status = "synced"
            storage_mode = "s3"
        else:
            # Offline mode: Save to local filesystem only
            storage_dir = self._entity_storage_dir(entity_type, entity_id, field_name)
            storage_dir.mkdir(parents=True, exist_ok=True)
            file_path = storage_dir / filename
            with open(file_path, "wb") as f:
                f.write(content)
            file_path = str(file_path)
            sync_status = "pending"
            storage_mode = "local"

        # Create DB record
        record = await self._create_record(
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            remote_url=remote_url,
            file_size=len(content),
            content_type=file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream",
            file_hash=file_hash,
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            company_id=company_id,
            storage_mode=storage_mode,
            sync_status=sync_status,
        )

        return {
            "file_id": record.id,
            "url": f"/api/files/{record.id}",
            "filename": filename,
            "original_filename": record.original_filename,
            "file_size": record.file_size,
            "content_type": record.content_type,
            "storage_mode": record.storage_mode,
            "sync_status": record.sync_status,
        }

    async def _deactivate_existing(self, entity_type: str, entity_id: str, field_name: str):
        session = get_db_session()
        rows = await session.execute(
            select(FileRecord).where(
                FileRecord.entity_type == entity_type,
                FileRecord.entity_id == entity_id,
                FileRecord.field_name == field_name,
                FileRecord.is_active == True,
            )
        )
        for rec in rows.scalars().all():
            rec.is_active = False
        await session.commit()

    async def _clone_link(
        self,
        src: FileRecord,
        entity_type: str,
        entity_id: str,
        field_name: str,
        company_id: Optional[str],
    ) -> Dict[str, Any]:
        session = get_db_session()
        clone = FileRecord(
            filename=src.filename,
            original_filename=src.original_filename,
            file_path=src.file_path,
            remote_url=src.remote_url,
            file_size=src.file_size,
            content_type=src.content_type,
            file_hash=src.file_hash,
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            company_id=company_id,
            storage_mode=src.storage_mode,
            sync_status=src.sync_status,
        )
        session.add(clone)
        await session.commit()
        await session.refresh(clone)
        return {
            "file_id": clone.id,
            "url": f"/api/files/{clone.id}",
            "filename": clone.filename,
            "original_filename": clone.original_filename,
            "file_size": clone.file_size,
            "content_type": clone.content_type,
            "storage_mode": clone.storage_mode,
            "sync_status": clone.sync_status,
            "reused_existing": True,
        }

    async def _create_record(
        self,
        filename: str,
        original_filename: str,
        file_path: Optional[str],
        remote_url: Optional[str],
        file_size: int,
        content_type: str,
        file_hash: str,
        entity_type: str,
        entity_id: str,
        field_name: str,
        company_id: Optional[str],
        storage_mode: str,
        sync_status: str,
    ) -> FileRecord:
        session = get_db_session()
        rec = FileRecord(
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            remote_url=remote_url,
            file_size=file_size,
            content_type=content_type,
            file_hash=file_hash,
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            company_id=company_id,
            storage_mode=storage_mode,
            sync_status=sync_status,
            synced_at=datetime.utcnow() if sync_status == "synced" else None,
        )
        session.add(rec)
        await session.commit()
        await session.refresh(rec)
        return rec


    async def get_file(self, file_id: str) -> Optional[FileRecord]:
        session = get_db_session()
        r = await session.execute(select(FileRecord).where(FileRecord.id == file_id))
        return r.scalar_one_or_none()

    async def get_entity_files(self, entity_type: str, entity_id: str) -> list[Dict[str, Any]]:
        """Get all active files for a specific entity"""
        session = get_db_session()
        result = await session.execute(
            select(FileRecord).where(
                FileRecord.entity_type == entity_type,
                FileRecord.entity_id == entity_id,
                FileRecord.is_active == True,
            )
        )
        files = result.scalars().all()
        return [{
            "file_id": f.id,
            "url": f"/api/files/{f.id}",
            "filename": f.filename,
            "original_filename": f.original_filename,
            "field_name": f.field_name,
            "file_size": f.file_size,
            "content_type": f.content_type,
            "storage_mode": f.storage_mode,
            "sync_status": f.sync_status,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        } for f in files]

    async def delete_file(self, file_id: str) -> bool:
        """
        Delete a file record. Physical file deletion occurs only if no other
        active records reference the same file hash.
        """
        session = get_db_session()
        r = await session.execute(select(FileRecord).where(FileRecord.id == file_id))
        rec = r.scalar_one_or_none()
        if not rec:
            return False
        rec.is_active = False
        
        # physical cleanup only if no other active refs to same hash
        other = await session.execute(
            select(FileRecord).where(
                FileRecord.file_hash == rec.file_hash,
                FileRecord.is_active == True,
                FileRecord.id != rec.id,
            )
        )
        if not other.scalar_one_or_none():
            # delete local file
            try:
                if rec.file_path and os.path.exists(rec.file_path):
                    os.remove(rec.file_path)
            except Exception:
                pass
            
            # delete S3 file
            try:
                if rec.remote_url:
                    bucket_part = f"{self.upload_service.s3_bucket_name}.s3.{self.upload_service.s3_region}.amazonaws.com/"
                    if bucket_part in rec.remote_url:
                        key = rec.remote_url.split(bucket_part, 1)[-1]
                        await self.upload_service.delete_from_s3(key)
            except Exception:
                pass
        
        await session.commit()
        return True

    async def sync_offline_to_online(self) -> Dict[str, Any]:
        """
        Sync offline files to online (S3).
        Uploads pending local files to S3 when switching from offline to online mode.
        """
        session = get_db_session()
        rows = await session.execute(
            select(FileRecord).where(
                FileRecord.sync_status == "pending",
                FileRecord.is_active == True,
                FileRecord.storage_mode == "local"
            )
        )
        items = rows.scalars().all()
        synced = 0
        errors: list[str] = []
        
        for rec in items:
            try:
                if not rec.file_path or not os.path.exists(rec.file_path):
                    errors.append(f"Missing local file: {rec.file_path}")
                    continue
                
                # Read local file
                async with aiofiles.open(rec.file_path, "rb") as f:
                    content = await f.read()
                
                # Upload to S3
                s3_path = f"{rec.entity_type}/{rec.entity_id}/{rec.field_name}/{rec.filename}"
                remote_url = await self.upload_service.upload_to_s3(
                    file_content=content,
                    destination_path=s3_path,
                    content_type=rec.content_type,
                )
                
                # Update record
                rec.remote_url = remote_url
                rec.sync_status = "synced"
                rec.storage_mode = "s3"
                rec.synced_at = datetime.utcnow()
                synced += 1
                
            except Exception as e:
                errors.append(f"Error syncing {rec.filename}: {str(e)}")
        
        await session.commit()
        return {
            "synced_count": synced,
            "errors": errors,
            "total_pending": len(items),
            "direction": "offline_to_online"
        }
    
    async def sync_online_to_offline(self) -> Dict[str, Any]:
        """
        Sync online files to offline (download from S3 to local).
        Downloads S3 files to local storage when switching from online to offline mode.
        """
        import aiohttp
        
        session = get_db_session()
        rows = await session.execute(
            select(FileRecord).where(
                FileRecord.is_active == True,
                FileRecord.storage_mode == "s3",
                FileRecord.remote_url.isnot(None)
            )
        )
        items = rows.scalars().all()
        synced = 0
        errors: list[str] = []
        
        async with aiohttp.ClientSession() as http_session:
            for rec in items:
                try:
                    if not rec.remote_url:
                        continue
                    
                    # Download from S3
                    async with http_session.get(rec.remote_url) as response:
                        if response.status != 200:
                            errors.append(f"Failed to download {rec.filename}: HTTP {response.status}")
                            continue
                        content = await response.read()
                    
                    # Save to local
                    storage_dir = self._entity_storage_dir(rec.entity_type, rec.entity_id, rec.field_name)
                    storage_dir.mkdir(parents=True, exist_ok=True)
                    file_path = storage_dir / rec.filename
                    with open(file_path, "wb") as f:
                        f.write(content)
                    
                    # Update record
                    rec.file_path = str(file_path)
                    rec.storage_mode = "local"
                    synced += 1
                    
                except Exception as e:
                    errors.append(f"Error syncing {rec.filename}: {str(e)}")
        
        await session.commit()
        return {
            "synced_count": synced,
            "errors": errors,
            "total_processed": len(items),
            "direction": "online_to_offline"
        }


