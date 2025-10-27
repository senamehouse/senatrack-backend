from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # APP Config
    PROJECT_NAME: str = "Senatrack"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "A FastAPI application with authentication"
    
    # Database Config / Modes
    LOCAL_DB_PATH: str = "local_data.db"
    DATABASE_MODE: str = os.getenv("DATABASE_MODE", "online")  # offline | online
    REMOTE_DB_URL: str | None = "postgresql+asyncpg://neondb_owner:npg_Rq2DfcZgTE8L@ep-bitter-glade-adb7cses-pooler.c-2.us-east-1.aws.neon.tech/neondb?ssl=require"
    COMPANY_ID: str | None = os.getenv("COMPANY_ID")  # required for tenant scoping
    AUTO_MIGRATE_REMOTE: bool = True
    
    # Server Config
    DEFAULT_HOST: str = "0.0.0.0"
    DEFAULT_PORT: int = 8000
    
    # Authentication Config
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 3000000000
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password Hashing
    PASSWORD_HASH_ALGORITHM: str = "bcrypt"  # bcrypt or argon2
    
    # Resend Config
    RESEND_API_KEY: str = ""

    # File Storage Config (uses DATABASE_MODE: online = S3, offline = local)
    LOCAL_FILES_PATH: str = os.getenv("LOCAL_FILES_PATH", "local_files")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", str(5 * 1024 * 1024)))
    # Allowed image MIME types
    ALLOWED_FILE_TYPES: list[str] = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
    ]

    # AWS Configuration
    AWS_ACCESS_KEY_ID: str = "AKIA4MTWK7S7J6BZW5WJ"
    AWS_SECRET_ACCESS_KEY: str = "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"
    AWS_BUCKET_NAME: str = "video-platform-aws"
    AWS_REGION: str = "us-east-1"

    class Config:
        env_file = ".env"

settings = Settings()