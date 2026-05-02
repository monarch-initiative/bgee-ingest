"""Print the BGee version (URL form, e.g. `15_2`) to stdout.

The justfile captures this and exports it as BGEE_VERSION before invoking
kghub-downloader, which substitutes `{BGEE_VERSION}` into the URLs in
download.yaml.
"""

from __future__ import annotations

import sys
from pathlib import Path

INGEST_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(INGEST_DIR / "src"))

from versions import resolve_version  # noqa: E402


if __name__ == "__main__":
    print(resolve_version())
