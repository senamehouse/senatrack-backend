from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # APP Config
    PROJECT_NAME: str = "Senatrack"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "A FastAPI application"
    # Firebase Config
    FIREBASE_SERVICE_ACCOUNT_KEY_PATH: str = os.path.join(os.path.dirname(__file__), "firebase_service_account_key.json")
    FIREBASE_PROJECT_ID: str = "senatrack"
    # Resend Config
    RESEND_API_KEY: str 

    class Config:
        env_file = ".env"

settings = Settings()