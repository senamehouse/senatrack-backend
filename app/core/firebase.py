import firebase_admin
from firebase_admin import credentials, firestore
from app.core.settings import settings

cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_KEY_PATH)
firebase_admin.initialize_app(cred)

# Initialize Firestore client 
db = firestore.client()

# Export firebase services

__all__ = ["db"]