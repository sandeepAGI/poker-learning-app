import os
from utils.logger import get_logger

logger = get_logger("config")

# Environment settings
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
logger.info(f"Running in {ENVIRONMENT} environment")

# API Settings
API_VERSION = "v1"
PORT = int(os.environ.get("PORT", "8080"))
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
RATE_LIMIT = int(os.environ.get("RATE_LIMIT", "60"))  # 60 requests per minute by default

# Security settings
SECRET_KEY = os.environ.get("SECRET_KEY", "development-secret-key-change-in-production")
if SECRET_KEY == "development-secret-key-change-in-production" and ENVIRONMENT == "production":
    logger.warning("Using default SECRET_KEY in production environment! This is a security risk.")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
JWT_ALGORITHM = "HS256"

# Session settings
SESSION_TIMEOUT_MINUTES = int(os.environ.get("SESSION_TIMEOUT_MINUTES", "30"))
CLEANUP_INTERVAL_SECONDS = int(os.environ.get("CLEANUP_INTERVAL_SECONDS", "300"))  # 5 minutes

# Game Settings
STARTING_CHIPS = int(os.environ.get("STARTING_CHIPS", "1000"))
SMALL_BLIND = int(os.environ.get("SMALL_BLIND", "5"))
BIG_BLIND = int(os.environ.get("BIG_BLIND", "10"))
BLIND_INCREASE = int(os.environ.get("BLIND_INCREASE", "5"))
BLIND_INCREASE_HANDS = int(os.environ.get("BLIND_INCREASE_HANDS", "10"))  # Increase blinds every 10 hands

# AI Settings
AI_PLAYER_COUNT = int(os.environ.get("AI_PLAYER_COUNT", "4"))
AI_PERSONALITIES = os.environ.get("AI_PERSONALITIES", "Conservative,Risk Taker,Probability-Based,Bluffer").split(",")