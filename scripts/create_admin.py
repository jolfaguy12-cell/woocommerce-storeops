#!/usr/bin/env python3
"""Create the first StoreOps Super Admin from environment variables."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "apps" / "core-server"
sys.path.insert(0, str(CORE))

from app.cli.create_admin import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
