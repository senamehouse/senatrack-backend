from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # APP Config
    PROJECT_NAME: str = "Senatrack"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "A FastAPI application with authentication"
    
    # Database Config
    LOCAL_DB_PATH: str = "local_data.db"
    SERVER_DB_PATH: str = "server_data.db"  # For server-side SQLite
    
    # Server Config
    DEFAULT_HOST: str = "0.0.0.0"
    DEFAULT_PORT: int = 8000
    
    # Authentication Config
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password Hashing
    PASSWORD_HASH_ALGORITHM: str = "bcrypt"  # bcrypt or argon2
    
    # Resend Config
    RESEND_API_KEY: str = ""

    class Config:
        env_file = ".env"

settings = Settings()