#!/usr/bin/env python
"""
Repo-root manage.py shim.

The real Django entrypoint lives at `src/manage.py` (Docker WORKDIR is `/src`).
This wrapper makes `python manage.py ...` work from the repo root in local dev/CI.
"""
from pathlib import Path
import runpy


if __name__ == "__main__":
    manage_py = Path(__file__).resolve().parent / "src" / "manage.py"
    runpy.run_path(str(manage_py), run_name="__main__")

