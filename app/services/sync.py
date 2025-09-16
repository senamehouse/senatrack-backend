import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.sync import SyncLog
from app.models.user import User as UserModel
from app.models.auth import RefreshToken
from app.services.user import UserService

logger = logging.getLogger(__name__)

class SyncService:
    """Service for synchronizing data between local and server SQLite databases"""
    
    def __init__(self):
        self.user_service = UserService()
        self.sync_in_progress = False
    
    async def get_unsynced_changes(self) -> List[Dict[str, Any]]:
        """Get all unsynced changes"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(SyncLog).where(SyncLog.synced == False)
                )
                sync_logs = result.scalars().all()
                
                changes = []
                for log in sync_logs:
                    change = {
                        'id': log.id,
                        'operation': log.operation,
                        'record_id': log.record_id,
                        'table_name': log.table_name,
                        'data': json.loads(log.data) if log.data else {}
                    }
                    # Add user fields for easier processing
                    if log.data:
                        user_data = json.loads(log.data)
                        change.update({
                            'name': user_data.get('name'),
                            'email': user_data.get('email'),
                            'phone_number': user_data.get('phone_number')
                        })
                    changes.append(change)
                return changes
        except Exception as e:
            logger.error(f"Error getting unsynced changes: {str(e)}")
            return []
    
    async def mark_sync_log_as_synced(self, log_id: int):
        """Mark a sync log entry as synced"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(SyncLog).where(SyncLog.id == log_id)
                )
                sync_log = result.scalar_one_or_none()
                
                if sync_log:
                    sync_log.synced = True
                    sync_log.synced_at = datetime.now()
                    await session.commit()
        except Exception as e:
            logger.error(f"Error marking sync log as synced: {str(e)}")
    
    async def clear_all_data(self):
        """Clear all data from database"""
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(delete(UserModel))
                await session.execute(delete(RefreshToken))
                await session.execute(delete(SyncLog))
                await session.commit()
        except Exception as e:
            logger.error(f"Error clearing all data: {str(e)}")
            raise
    
    async def sync_to_server(self) -> Dict[str, Any]:
        """
        Sync local changes to server database
        
        Returns:
            Dict with sync results
        """
        if self.sync_in_progress:
            return {"status": "error", "message": "Sync already in progress"}
        
        self.sync_in_progress = True
        results = {
            "status": "success",
            "synced_records": 0,
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Get unsynced changes from local database
            unsynced_changes = await self.get_unsynced_changes()
            
            if not unsynced_changes:
                results["message"] = "No changes to sync"
                return results
            
            # Process each change
            for change in unsynced_changes:
                try:
                    if change['operation'] == 'CREATE':
                        user_data = {
                            'name': change['name'],
                            'email': change['email'],
                            'phone_number': change['phone_number']
                        }
                        await self.user_service.create_user(user_data)
                        
                    elif change['operation'] == 'UPDATE':
                        user_data = {
                            'name': change['name'],
                            'email': change['email'],
                            'phone_number': change['phone_number']
                        }
                        await self.user_service.update_user(change['record_id'], user_data)
                        
                    elif change['operation'] == 'DELETE':
                        await self.user_service.delete_user(change['record_id'])
                    
                    # Mark as synced in local database
                    await self.mark_sync_log_as_synced(change['id'])
                    results["synced_records"] += 1
                    
                except Exception as e:
                    error_msg = f"Error syncing {change['operation']} for {change['record_id']}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
            
            results["message"] = f"Synced {results['synced_records']} records"
            
        except Exception as e:
            results["status"] = "error"
            results["message"] = f"Sync failed: {str(e)}"
            logger.error(f"Sync to server failed: {str(e)}")
        
        finally:
            self.sync_in_progress = False
        
        return results
    
    async def sync_from_server(self) -> Dict[str, Any]:
        """
        Sync server data to local database
        
        Returns:
            Dict with sync results
        """
        if self.sync_in_progress:
            return {"status": "error", "message": "Sync already in progress"}
        
        self.sync_in_progress = True
        results = {
            "status": "success",
            "synced_records": 0,
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Get all data from server database
            server_data = await self.user_service.export_data()
            
            if not server_data:
                results["message"] = "No data to sync from server"
                return results
            
            # Sync to local database
            success = await self.user_service.sync_data(server_data)
            
            if success:
                results["synced_records"] = len(server_data)
                results["message"] = f"Synced {len(server_data)} records from server"
            else:
                results["status"] = "error"
                results["message"] = "Failed to sync data to local database"
                
        except Exception as e:
            results["status"] = "error"
            results["message"] = f"Sync from server failed: {str(e)}"
            logger.error(f"Sync from server failed: {str(e)}")
        
        finally:
            self.sync_in_progress = False
        
        return results
    
    async def bidirectional_sync(self) -> Dict[str, Any]:
        """
        Perform bidirectional sync between local and server databases
        
        Returns:
            Dict with sync results
        """
        results = {
            "status": "success",
            "sync_to_server": {},
            "sync_from_server": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # First sync local changes to server
            results["sync_to_server"] = await self.sync_to_server()
            
            # Then sync server changes to local
            results["sync_from_server"] = await self.sync_from_server()
            
            # Determine overall status
            if (results["sync_to_server"]["status"] == "error" or 
                results["sync_from_server"]["status"] == "error"):
                results["status"] = "partial_success"
            
            results["message"] = "Bidirectional sync completed"
            
        except Exception as e:
            results["status"] = "error"
            results["message"] = f"Bidirectional sync failed: {str(e)}"
            logger.error(f"Bidirectional sync failed: {str(e)}")
        
        return results
    
    async def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        try:
            unsynced_changes = await self.get_unsynced_changes()
            local_count = await self.user_service.get_users_count()
            
            return {
                "status": "success",
                "local_records": local_count,
                "unsynced_changes": len(unsynced_changes),
                "sync_in_progress": self.sync_in_progress,
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get sync status: {str(e)}"
            }
    
    async def force_sync_all(self) -> Dict[str, Any]:
        """
        Force sync all data (overwrites local with server data)
        
        Returns:
            Dict with sync results
        """
        results = {
            "status": "success",
            "synced_records": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Get all data from server
            server_data = await self.user_service.export_data()
            
            # Clear local database and sync all data
            await self.clear_all_data()
            success = await self.user_service.sync_data(server_data)
            
            if success:
                results["synced_records"] = len(server_data)
                results["message"] = f"Force synced {len(server_data)} records"
            else:
                results["status"] = "error"
                results["message"] = "Failed to force sync data"
                
        except Exception as e:
            results["status"] = "error"
            results["message"] = f"Force sync failed: {str(e)}"
            logger.error(f"Force sync failed: {str(e)}")
        
        return results
