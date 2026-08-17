#!/usr/bin/env python3
"""Compress PNG/JPEG images in the repo in place, tracking progress in a JSON manifest.

Re-running is safe and cheap: a file is only recompressed if its current
content hash doesn't match the hash recorded for it after its last
compression (i.e. it's new, or someone replaced it with a fresh original).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = Path(__file__).resolve().parent / "image_compression_manifest.json"
EXCLUDE_DIR_NAMES = {".git", "dist"}
PNG_EXTS = {".png"}
JPEG_EXTS = {".jpg", ".jpeg"}


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_images(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
            continue
        ext = path.suffix.lower()
        if ext in PNG_EXTS or ext in JPEG_EXTS:
            yield path


def compress_png(src: Path, tmp_path: Path, quality_range: str) -> bool:
    """Write a quantized copy of src to tmp_path. Returns True on success."""
    result = subprocess.run(
        [
            "pngquant",
            "--quality", quality_range,
            "--strip",
            "--force",
            "--output", str(tmp_path),
            str(src),
        ],
        capture_output=True,
    )
    # pngquant exits 99 when it can't hit the quality floor; treat as "no change".
    return result.returncode == 0 and tmp_path.exists()


def compress_jpeg(src: Path, tmp_path: Path, quality: int) -> bool:
    with Image.open(src) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(tmp_path, "JPEG", quality=quality, optimize=True, progressive=True)
    return tmp_path.exists()


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r") as f:
            return json.load(f)
    return {}


def save_manifest(manifest: dict) -> None:
    tmp = MANIFEST_PATH.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")
    tmp.replace(MANIFEST_PATH)


def human(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}GB"


def process_one(path: Path, manifest: dict, png_quality: str, jpeg_quality: int, dry_run: bool):
    rel = path.relative_to(REPO_ROOT).as_posix()
    current_hash = sha256_of_file(path)
    entry = manifest.get(rel)

    if entry and entry.get("compressed_hash") == current_hash:
        return "skipped", 0

    original_size = path.stat().st_size
    ext = path.suffix.lower()
    fd, tmp_name = tempfile.mkstemp(suffix=ext)
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        if ext in PNG_EXTS:
            ok = compress_png(path, tmp_path, png_quality)
            tool = "pngquant"
        else:
            ok = compress_jpeg(path, tmp_path, jpeg_quality)
            tool = "pillow-jpeg"

        if not ok or tmp_path.stat().st_size == 0:
            new_size = original_size
            final_hash = current_hash
        else:
            new_size = tmp_path.stat().st_size
            if new_size < original_size:
                if not dry_run:
                    shutil.copystat(path, tmp_path, follow_symlinks=True)
                    tmp_path.replace(path)
                final_hash = sha256_of_file(path) if not dry_run else current_hash
            else:
                new_size = original_size
                final_hash = current_hash
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    saved = original_size - new_size
    saved_pct = (saved / original_size * 100) if original_size else 0.0
    if not dry_run:
        manifest[rel] = {
            "original_size": human(original_size),
            "compressed_size": human(new_size),
            "saved": human(saved),
            "saved_pct": f"{saved_pct:.1f}%",
            "compressed_hash": final_hash,
            "tool": tool,
            "compressed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    return "compressed", saved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(REPO_ROOT), help="Directory to scan (default: repo root)")
    parser.add_argument("--png-quality", default="65-85", help="pngquant quality range (default: 65-85)")
    parser.add_argument("--jpeg-quality", type=int, default=80, help="JPEG quality 1-95 (default: 80)")
    parser.add_argument("--dry-run", action="store_true", help="Report savings without writing files or manifest")
    args = parser.parse_args()

    if shutil.which("pngquant") is None:
        sys.exit("pngquant not found on PATH. Install it (e.g. `brew install pngquant`) and retry.")

    root = Path(args.root).resolve()
    manifest = load_manifest()

    n_compressed = n_skipped = n_unchanged = 0
    total_saved = 0

    for path in iter_images(root):
        status, saved = process_one(path, manifest, args.png_quality, args.jpeg_quality, args.dry_run)
        rel = path.relative_to(REPO_ROOT).as_posix()
        if status == "skipped":
            n_skipped += 1
        elif saved > 0:
            n_compressed += 1
            total_saved += saved
            print(f"  {rel}: -{human(saved)}")
        else:
            n_unchanged += 1

    if not args.dry_run:
        save_manifest(manifest)

    print()
    print(f"Compressed: {n_compressed}   Already reduced (skipped): {n_skipped}   No gain: {n_unchanged}")
    print(f"Total saved this run: {human(total_saved)}")
    if args.dry_run:
        print("(dry run — no files or manifest were changed)")


if __name__ == "__main__":
    main()
