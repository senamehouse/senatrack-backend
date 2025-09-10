from pydantic import BaseModel
from datetime import datetime

class User(BaseModel):
    id: str
    name: str
    email: str
    phone_number: str
    created_at: datetime
    updated_at: datetime

