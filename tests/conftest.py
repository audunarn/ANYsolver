"""Shared pytest configuration.

PyCharm may launch pytest with ``tests`` as the process working directory,
while several integration tests intentionally execute repository scripts by
relative path.  Normalize the working directory once for the full session so
those tests behave identically from PyCharm, PowerShell and CI.
"""

from __future__ import annotations

import os
from pathlib import Path


_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
os.chdir(_REPOSITORY_ROOT)
