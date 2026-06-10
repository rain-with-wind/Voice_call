"""@file __init__.py
@brief Flask application factory for the public room coordination backend.
"""

from flask import Flask, jsonify, request

from .config import Config
from .database import ensure_database, init_app as init_database
from .routes.health import bp as health_bp
from .routes.rooms import bp as rooms_bp
from .routes.voice import bp as voice_bp, init_sock


def create_app():
    """@brief Build and configure the Flask application instance.

    @return Flask Fully configured backend application.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    init_database(app)
    ensure_database(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(voice_bp)
    init_sock(app)

    @app.after_request
    def add_headers(response):
        """@brief Attach CORS headers to every outgoing response.

        @param response Flask response object.
        @return Response Updated response object.
        """
        origin = app.config["ALLOWED_ORIGIN"]
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, X-Manage-Token, X-Participant-Token, X-Device-Token"
        )
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return response

    @app.before_request
    def handle_options():
        """@brief Return an empty success payload for preflight requests.

        @return Response|None Immediate response for OPTIONS, otherwise `None`.
        """
        if request.method == "OPTIONS":
            return jsonify({"ok": True})
        return None

    @app.get("/")
    def index():
        """@brief Return a minimal root payload for CLI-first deployments."""
        return jsonify(
            {
                "ok": True,
                "service": "public-voice-call-backend",
                "mode": "cli-only",
                "health": "/api/health",
            }
        )

    return app
