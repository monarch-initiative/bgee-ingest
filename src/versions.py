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

# Must be the `www.` host: the bare `bgee.org` apex sits behind a Cloudflare
# managed challenge that returns HTTP 403 (`cf-mitigated: challenge`) to every
# non-browser client regardless of User-Agent. `www.bgee.org` serves the same
# files with no challenge.
BGEE_FTP_INDEX = "https://www.bgee.org/ftp/"
EXPR_CALLS_PATH = "download/calls/expr_calls/"
SENTINEL_HREF_PATTERN = re.compile(r'href="[^"]+_expr_(?:simple|advanced)\.tsv\.gz"')


def _list_versioned_dirs(timeout: int = 15) -> list[tuple[int, int]]:
    r = requests.get(BGEE_FTP_INDEX, timeout=timeout)
    r.raise_for_status()
    seen: set[tuple[int, int]] = set()
    for match in re.finditer(r'href="bgee_v(\d+)_(\d+)/"', r.text):
        seen.add((int(match.group(1)), int(match.group(2))))
    return sorted(seen)


def _has_expr_calls(major: int, minor: int, timeout: int = 10) -> bool:
    """True only if this version actually publishes expression call files.

    Note bgee.org answers unknown FTP paths with the site's single-page app
    under HTTP 200 rather than a 404, so a status check alone cannot tell a
    real directory from a missing one. The sentinel href search is what makes
    this reliable: the SPA contains no `*_expr_simple.tsv.gz` links. As of
    Bgee 16.0 this matters in practice -- 16.0 ships only `h5ad/` and
    `processed_expr_values/`, and every `calls/` path under it soft-200s.
    """
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
    into download.yaml. Automatically adopts a new Bgee release as soon as that
    release publishes expression calls.

    Raises on failure rather than falling back to a pinned version. A pinned
    fallback cannot rescue a build -- the downloads target the same host that
    just failed the probe -- it only hides the cause and lets the build report
    an upstream version it never actually verified.
    """
    candidates = _list_versioned_dirs()
    for major, minor in reversed(candidates):
        if _has_expr_calls(major, minor):
            return f"{major}_{minor}"
    raise RuntimeError(
        f"No Bgee version under {BGEE_FTP_INDEX} publishes expression calls "
        f"at {EXPR_CALLS_PATH} (checked: {candidates or 'none found'})."
    )


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
