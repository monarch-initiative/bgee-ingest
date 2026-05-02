"""Upstream source version fetcher for bgee-ingest.

BGee URLs encode the release version in their path (e.g. `bgee_v15_0`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kozahub_metadata_schema import (
    now_iso,
    urls_from_download_yaml,
    version_from_url_path,
)


INGEST_DIR = Path(__file__).resolve().parents[1]
DOWNLOAD_YAML = INGEST_DIR / "download.yaml"


def get_source_versions() -> list[dict[str, Any]]:
    urls = urls_from_download_yaml(DOWNLOAD_YAML)
    raw, method = version_from_url_path(urls[0] if urls else "", r"/bgee_v(\d+_\d+)/")
    # Convert "15_0" → "15.0" so it reads as a normal semver-ish label.
    version = raw.replace("_", ".") if raw != "unknown" else raw
    return [
        {
            "id": "infores:bgee",
            "name": "BGee — Gene Expression",
            "urls": urls,
            "version": version,
            "version_method": method,
            "retrieved_at": now_iso(),
        }
    ]
