"""
Newcomer Navigation — project root entry point.

The real application lives in `backend/app/`, kept modular as separate
routers, services and models. This file is the convenience launcher the
project already expected at the root:

    python main.py

It adds `backend/` to the import path, loads `backend/.env`, and serves
`backend/app/main.py`'s FastAPI app with uvicorn.

Equivalent (and preferred for development, since --reload behaves better
when run from the app's own directory):

    cd backend
    uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent / "backend"

if not BACKEND_DIR.is_dir():
    raise SystemExit(
        "Could not find the ./backend directory next to main.py.\n"
        "Make sure the backend ZIP was extracted into the project root."
    )

# Make `app.*` importable, and resolve the relative sqlite path in
# DATABASE_URL against backend/ rather than the current working directory.
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)


def main() -> None:
    try:
        import uvicorn
    except ModuleNotFoundError:
        raise SystemExit(
            "uvicorn is not installed.\n"
            "Run:  pip install -r backend/requirements.txt"
        )

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    reload_enabled = os.environ.get("RELOAD", "true").lower() in ("1", "true", "yes")

    print(f"Newcomer Navigation API -> http://{host}:{port}  (docs at /docs)")
    uvicorn.run("app.main:app", host=host, port=port, reload=reload_enabled)


if __name__ == "__main__":
    main()
