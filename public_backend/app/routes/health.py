from datetime import datetime, timezone
import platform

from flask import Blueprint, jsonify


bp = Blueprint("health", __name__, url_prefix="/api")


@bp.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "public-voice-backend",
            "time": datetime.now(timezone.utc).isoformat(),
            "platform": platform.platform(),
        }
    )
