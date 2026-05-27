#!/usr/bin/env python3
"""
Get Going Fast | Lens Turbo model downloader

Downloads the Hugging Face model and kernel repos into the local cache folders
used by the Lens Turbo app.

This script is intentionally separate from the installer BAT so the BAT stays
simple and the download behavior is easier to maintain.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable


MODEL_REPO = "WaveCut/Lens-Turbo-SDNQ-uint4-static"
KERNEL_REPO = "kernels-community/gpt-oss-triton-kernels"


def app_root() -> Path:
    return Path(__file__).resolve().parent


APP_DIR = app_root()
MODELS_ROOT = APP_DIR / "models" / "lens"
HF_HUB_CACHE = Path(os.environ.get("HF_HUB_CACHE", MODELS_ROOT / "hf_cache"))
KERNELS_CACHE = Path(os.environ.get("KERNELS_CACHE_DIR", MODELS_ROOT / "kernels_cache"))
TMP_DIR = Path(os.environ.get("TMP_DIR", APP_DIR / "tmp"))


def repo_cache_name(repo_id: str, prefix: str = "models") -> str:
    owner, name = repo_id.split("/", 1)
    return f"{prefix}--{owner}--{name}"


def api_url(repo_id: str) -> str:
    return f"https://huggingface.co/api/models/{repo_id}"


def file_url(repo_id: str, revision: str, filename: str) -> str:
    return f"https://huggingface.co/{repo_id}/resolve/{revision}/{filename}"


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "GGF-Lens-Turbo-Downloader/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def iter_files(meta: dict) -> Iterable[str]:
    for sibling in meta.get("siblings", []):
        filename = sibling.get("rfilename")
        if not filename:
            continue
        if filename.endswith(".gitattributes"):
            continue
        yield filename


def download_file(url: str, out_path: Path, retries: int = 4) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists() and out_path.stat().st_size > 0:
        print(f"  exists: {out_path.name}")
        return

    tmp_path = out_path.with_suffix(out_path.suffix + ".part")

    for attempt in range(1, retries + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "GGF-Lens-Turbo-Downloader/1.0"})
            with urllib.request.urlopen(request, timeout=120) as response, tmp_path.open("wb") as f:
                total = response.headers.get("Content-Length")
                total_mb = int(total) / 1024 / 1024 if total and total.isdigit() else None
                if total_mb:
                    print(f"  downloading: {out_path.name} ({total_mb:.1f} MB)")
                else:
                    print(f"  downloading: {out_path.name}")

                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)

            tmp_path.replace(out_path)
            return

        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            if attempt >= retries:
                raise RuntimeError(f"Failed to download {url}: {exc}") from exc
            wait = 2 * attempt
            print(f"  retrying in {wait}s after download error: {exc}")
            time.sleep(wait)


def download_hf_repo(repo_id: str, cache_root: Path, cache_prefix: str, label: str) -> None:
    cache_root.mkdir(parents=True, exist_ok=True)

    repo_dir = cache_root / repo_cache_name(repo_id, cache_prefix)
    refs_dir = repo_dir / "refs"
    ref_file = refs_dir / "main"

    if ref_file.exists() and ref_file.read_text(encoding="utf-8").strip():
        print(f"{label} cache already present for {repo_id}.")
        return

    print(f"Fetching {label} file list for {repo_id}...")
    meta = fetch_json(api_url(repo_id))
    sha = meta.get("sha") or meta.get("lastModified") or "main"

    snapshot_dir = repo_dir / "snapshots" / sha
    refs_dir.mkdir(parents=True, exist_ok=True)
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    files = list(iter_files(meta))
    if not files:
        raise RuntimeError(f"No downloadable files found for {repo_id}")

    print(f"Downloading {len(files)} {label} file(s) for {repo_id}...")
    for filename in files:
        out_path = snapshot_dir / filename
        download_file(file_url(repo_id, "main", filename), out_path)

    ref_file.write_text(str(sha), encoding="utf-8")
    print(f"{label.capitalize()} download complete: {repo_id}")


def main() -> int:
    print("Get Going Fast | Lens Turbo model downloader")
    print()

    TMP_DIR.mkdir(parents=True, exist_ok=True)

    try:
        download_hf_repo(
            repo_id=MODEL_REPO,
            cache_root=HF_HUB_CACHE,
            cache_prefix="models",
            label="model",
        )
        download_hf_repo(
            repo_id=KERNEL_REPO,
            cache_root=KERNELS_CACHE,
            cache_prefix="kernels",
            label="kernel",
        )
    except Exception as exc:
        print()
        print(f"Model download failed: {exc}")
        return 1

    print()
    print("All model downloads are complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
