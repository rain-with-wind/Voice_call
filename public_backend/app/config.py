import os
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
DEFAULT_DB = DATA_DIR / "public_voice_call.db"


class Config:
    HOST = os.getenv("PUBLIC_VOICE_BACKEND_HOST", "0.0.0.0")
    PORT = int(os.getenv("PUBLIC_VOICE_BACKEND_PORT", "8100"))
    DATABASE_PATH = os.getenv("PUBLIC_VOICE_BACKEND_DB", str(DEFAULT_DB))
    ALLOWED_ORIGIN = os.getenv("PUBLIC_VOICE_ALLOWED_ORIGIN", "*")
    ROOM_TTL_SECONDS = int(os.getenv("PUBLIC_VOICE_ROOM_TTL_SECONDS", "120"))
    HEARTBEAT_INTERVAL_SECONDS = int(os.getenv("PUBLIC_VOICE_HEARTBEAT_INTERVAL_SECONDS", "30"))
    PARTICIPANT_TTL_SECONDS = int(os.getenv("PUBLIC_VOICE_PARTICIPANT_TTL_SECONDS", "90"))
    MESSAGE_LIMIT = int(os.getenv("PUBLIC_VOICE_MESSAGE_LIMIT", "80"))
