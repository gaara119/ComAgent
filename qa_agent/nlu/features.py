"""Request-local, explicit ablation switches; defaults enable the maintained path."""
from __future__ import annotations

import os


def enabled(name: str) -> bool:
    false={"0", "false", "off", "no"}
    return os.getenv(name,"true").strip().lower() not in false
