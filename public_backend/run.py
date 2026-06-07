from pathlib import Path
import os
import sys


CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from public_backend.app import create_app


app = create_app()


if __name__ == "__main__":
    debug = os.getenv("PUBLIC_VOICE_BACKEND_DEBUG", "0") == "1"
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=debug)
