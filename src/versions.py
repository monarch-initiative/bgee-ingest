"""Upstream source version fetcher for bgee-ingest.

The BGee version is resolved at build time by probing the FTP listing for
the highest `bgee_vMAJOR_MINOR/` directory that actually contains expression
call data, then injected into download.yaml URLs as the `BGEE_VERSION` env
var (consumed by kghub-downloader's `{VAR}` substitution). The same value
is reported back here so the metadata file always reflects the version that
was actually downloaded.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import requests

from kozahub_metadata_schema import now_iso, urls_from_download_yaml


INGEST_DIR = Path(__file__).resolve().parents[1]
DOWNLOAD_YAML = INGEST_DIR / "download.yaml"

BGEE_FTP_INDEX = "https://bgee.org/ftp/"
EXPR_CALLS_PATH = "download/calls/expr_calls/"
SENTINEL_HREF_PATTERN = re.compile(r'href="[^"]+_expr_(?:simple|advanced)\.tsv\.gz"')

# Used if the probe fails (network down, layout changed). Should match the
# version baked into download.yaml fallback expectations.
FALLBACK_VERSION_URL_FORM = "15_2"


def _list_versioned_dirs(timeout: int = 15) -> list[tuple[int, int]]:
    r = requests.get(BGEE_FTP_INDEX, timeout=timeout)
    r.raise_for_status()
    seen: set[tuple[int, int]] = set()
    for match in re.finditer(r'href="bgee_v(\d+)_(\d+)/"', r.text):
        seen.add((int(match.group(1)), int(match.group(2))))
    return sorted(seen)


def _has_expr_calls(major: int, minor: int, timeout: int = 10) -> bool:
    url = f"{BGEE_FTP_INDEX}bgee_v{major}_{minor}/{EXPR_CALLS_PATH}"
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code != 200:
            return False
        return bool(SENTINEL_HREF_PATTERN.search(r.text))
    except requests.RequestException:
        return False


def latest_bgee_version() -> str:
    """Return the highest bgee_vM_N directory that contains expression call data.

    Returns the version in URL-form (e.g. `"15_2"`), suitable for substitution
    into download.yaml. Falls back to FALLBACK_VERSION_URL_FORM if the probe
    fails so CI doesn't break when bgee.org is unreachable.
    """
    try:
        candidates = _list_versioned_dirs()
    except requests.RequestException:
        return FALLBACK_VERSION_URL_FORM
    for major, minor in reversed(candidates):
        if _has_expr_calls(major, minor):
            return f"{major}_{minor}"
    return FALLBACK_VERSION_URL_FORM


def resolve_version() -> str:
    """Return BGEE_VERSION from env if set, otherwise probe."""
    return os.environ.get("BGEE_VERSION") or latest_bgee_version()


def get_source_versions() -> list[dict[str, Any]]:
    version_url_form = resolve_version()
    version = version_url_form.replace("_", ".")
    # urls_from_download_yaml reads the static URLs verbatim; expand the
    # {BGEE_VERSION} placeholder for the metadata record so consumers see
    # the resolved URLs that were actually fetched.
    raw_urls = urls_from_download_yaml(DOWNLOAD_YAML)
    urls = [u.replace("{BGEE_VERSION}", version_url_form) for u in raw_urls]
    return [
        {
            "id": "infores:bgee",
            "name": "BGee — Gene Expression",
            "urls": urls,
            "version": version,
            "version_method": "ftp_index_probe",
            "retrieved_at": now_iso(),
        }
    ]
