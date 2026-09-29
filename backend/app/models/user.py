from beanie import Document, Indexed
from pydantic import EmailStr, Field
from datetime import datetime
from typing import Optional
import pymongo


class User(Document):
    email: Indexed(EmailStr, unique=True)
    username: str
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
        indexes = [
            [("email", pymongo.ASCENDING)],
            [("created_at", pymongo.DESCENDING)],
        ]
