import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "app.db"
DRINKS_CONFIG = BASE_DIR / "configs" / "drinks.yaml"
MODELS_DIR = BASE_DIR / "models"
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"

SECRET_KEY = os.environ.get("VENDING_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 720

CAMERA_ID = int(os.environ.get("CAMERA_ID", "0"))
CAMERA_WIDTH = 960
CAMERA_HEIGHT = 540
JPEG_QUALITY = 70
