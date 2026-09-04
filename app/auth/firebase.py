import logging
from pathlib import Path
from typing import Optional, Dict, Any
import firebase_admin
from firebase_admin import credentials, auth

logger = logging.getLogger(__name__)

_FIREBASE_INITIALIZED = False

def init_firebase_admin() -> bool:
    global _FIREBASE_INITIALIZED
    if _FIREBASE_INITIALIZED:
        return True

    try:
        if len(firebase_admin._apps) > 0:
            _FIREBASE_INITIALIZED = True
            return True

        cert_path = Path(__file__).resolve().parent.parent.parent / "firebase_service_account.json"
        if cert_path.exists():
            cred = credentials.Certificate(str(cert_path))
            firebase_admin.initialize_app(cred)
            _FIREBASE_INITIALIZED = True
            logger.info("Firebase Admin initialized successfully using service account JSON.")
            return True
        else:
            logger.warning(f"Firebase service account file not found at {cert_path}")
            return False
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
        return False

def verify_firebase_id_token(id_token: str) -> Optional[Dict[str, Any]]:
    """
    Verifies a Firebase ID token and returns decoded claims if valid.
    """
    if not init_firebase_admin():
        logger.error("Firebase Admin is not initialized.")
        return None

    try:
        decoded_token = auth.verify_id_token(id_token, check_revoked=False)
        return decoded_token
    except Exception as e:
        logger.error(f"Error verifying Firebase ID token: {e}")
        return None
