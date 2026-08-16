#!/usr/bin/env python3
"""Build the downloadable Japanese world pack from the repository source tree."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile


REQUIRED_ROOTS = ("images", "characters", "content", "lessons", "audio")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _entry_name(relative: Path) -> str:
    """Return a safe ZIP entry name below the `ja/` pack root."""
    parts = PurePosixPath(*relative.parts).parts
    if not parts or any(part in ("", ".", "..") for part in parts):
        raise ValueError(f"unsafe world-pack path: {relative}")
    return "/".join(("ja", *parts))


def build_pack(*, source: Path, output: Path, version: str) -> None:
    source = Path(source).resolve()
    output = Path(output)
    if not source.is_dir():
        raise ValueError(f"world-pack source is not a directory: {source}")

    files: dict[str, dict[str, int | str]] = {}
    payloads: list[tuple[str, bytes]] = []
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symlinks are not allowed in world pack: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        entry = _entry_name(relative)
        data = path.read_bytes()
        relative_key = PurePosixPath(*relative.parts).as_posix()
        files[relative_key] = {"sha256": _sha256(data), "bytes": len(data)}
        payloads.append((entry, data))

    manifest = {
        "version": version,
        "requiredRoots": list(REQUIRED_ROOTS),
        "files": files,
    }
    manifest_bytes = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for entry, data in payloads:
            archive.writestr(entry, data)
        archive.writestr("ja/manifest.json", manifest_bytes)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("assets/ja"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    build_pack(source=args.source, output=args.output, version=args.version)


if __name__ == "__main__":
    main()
