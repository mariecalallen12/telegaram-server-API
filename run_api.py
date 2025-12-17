"""Convenient entrypoint for running the API from source.

This repo uses a `src/` layout. When running from source (without installing as a package),
Python doesn't automatically include `src/` on `sys.path`.

Use:
  python run_api.py
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from api.main import app  # noqa: E402

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)


