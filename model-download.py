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
import subprocess
import urllib.request
from pathlib import Path
from typing import Iterable

# Set Hugging Face environment defaults before imports
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "60"
os.environ["HF_HUB_ETAG_TIMEOUT"] = "60"

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


def download_file(url: str, out_path: Path, retries: int = 4, repo_id: str | None = None, filename: str | None = None) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if file exists and has content
    if out_path.exists() and out_path.stat().st_size > 0:
        print(f"  exists: {out_path.name}")
        return

    aria2c_bin = APP_DIR / "aria2c.exe"
    is_large = False
    try:
        # Try to get size for heuristic
        request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "GGF-Lens-Turbo-Downloader/1.0"})
        with urllib.request.urlopen(request, timeout=10) as resp:
            size = int(resp.headers.get("Content-Length", 0))
            if size > 1024 * 1024 * 1024: # 1GB
                is_large = True
    except Exception:
        pass

    # Stage 1: Fast aria2c (if not large)
    if aria2c_bin.exists() and not is_large:
        print(f"  Stage 1: Fast aria2c mode: {out_path.name}")
        try:
            cmd = [
                str(aria2c_bin), "--console-log-level=warn", "--summary-interval=20",
                "-x", "5", "-s", "5", "-j", "5", "-k", "1M", "--continue=true",
                "--max-tries=8", "--retry-wait=5", "--check-certificate=false",
                "--dir", str(out_path.parent), "--out", out_path.name, url
            ]
            subprocess.run(cmd, check=True)
            return
        except subprocess.CalledProcessError:
            print(f"  Fast aria2 failed, retrying safe single-connection mode for {out_path.name}")

    # Stage 2: Safe aria2c
    if aria2c_bin.exists():
        print(f"  Stage 2: Safe aria2c mode: {out_path.name}")
        try:
            cmd = [
                str(aria2c_bin), "--console-log-level=warn", "--summary-interval=30",
                "-x", "1", "-s", "1", "-j", "1", "-k", "1M", "--continue=true",
                "--max-tries=20", "--retry-wait=10", "--timeout=60", "--connect-timeout=30",
                "--lowest-speed-limit=50K", "--check-certificate=false",
                "--dir", str(out_path.parent), "--out", out_path.name, url
            ]
            subprocess.run(cmd, check=True)
            return
        except subprocess.CalledProcessError:
            print(f"  Safe aria2 failed, falling back to Hugging Face Python downloader for {out_path.name}")

    # Stage 3: huggingface_hub fallback
    if repo_id and filename:
        print(f"  Stage 3: huggingface_hub mode: {out_path.name}")
        try:
            from huggingface_hub import hf_hub_download
            hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=str(out_path.parent),
                local_dir_use_symlinks=False,
                resume_download=True,
            )
            return
        except Exception as e:
            print(f"  Hugging Face Python downloader failed: {e}")

    # Stage 4: Ultimate urllib fallback
    print(f"  Stage 4: urllib fallback mode: {out_path.name}")
    import ssl
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    tmp_path = out_path.with_suffix(out_path.suffix + ".part")

    for attempt in range(1, retries + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "GGF-Lens-Turbo-Downloader/1.0"})
            opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=context))
            with opener.open(request, timeout=120) as response, tmp_path.open("wb") as f:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk: break
                    f.write(chunk)
            tmp_path.replace(out_path)
            return
        except Exception as exc:
            if attempt >= retries:
                print(f"\n[ERROR] All download methods failed for: {out_path}")
                print(f"Direct URL: {url}")
                print("If this continues, disable VPN, antivirus HTTPS scanning, or split tunneling for huggingface.co, hf.co, cdn-lfs.huggingface.co, cas-bridge.xethub.hf.co, and xethub.hf.co.\n")
                raise RuntimeError(f"Failed to download {url}: {exc}")
            time.sleep(5 * attempt)


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
        download_file(
            url=file_url(repo_id, "main", filename),
            out_path=out_path,
            repo_id=repo_id,
            filename=filename
        )

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
