"""@file __init__.py
@brief Flask application factory for the public room coordination backend.
"""

from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from .config import Config
from .database import ensure_database, init_app as init_database
from .routes.health import bp as health_bp
from .routes.rooms import bp as rooms_bp


def create_app():
    """@brief Build and configure the Flask application instance.

    @return Flask Fully configured backend application.
    """
    frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
    app = Flask(__name__, static_folder=str(frontend_dir / "assets"), static_url_path="/assets")
    app.config.from_object(Config)

    init_database(app)
    ensure_database(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(rooms_bp)

    @app.after_request
    def add_headers(response):
        """@brief Attach CORS headers to every outgoing response.

        @param response Flask response object.
        @return Response Updated response object.
        """
        origin = app.config["ALLOWED_ORIGIN"]
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Manage-Token"
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
        """@brief Serve the single-page frontend entry document."""
        return send_from_directory(frontend_dir, "index.html")

    @app.get("/room/<room_code>")
    def room_page(room_code):
        """@brief Serve the frontend for room-detail deep links.

        @param room_code Room code embedded in the URL path.
        @return Response Frontend HTML document.
        """
        return send_from_directory(frontend_dir, "index.html")

    return app
