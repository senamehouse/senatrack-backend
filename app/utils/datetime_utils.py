from datetime import datetime
from typing import Optional

def convert_firestore_timestamp(timestamp) -> datetime:
    """Convert Firestore timestamp to Python datetime"""
    if timestamp and hasattr(timestamp, 'to_pydatetime'):
        return timestamp.to_pydatetime()
    elif timestamp is None:
        return datetime.now()
    return timestamp

def convert_timestamps(data: dict) -> tuple[datetime, datetime]:
    """Convert created_at and updated_at timestamps from user data"""
    created_at = convert_firestore_timestamp(data.get('created_at'))
    updated_at = convert_firestore_timestamp(data.get('updated_at'))
    return created_at, updated_at
