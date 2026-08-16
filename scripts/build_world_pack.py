#!/usr/bin/env python3
"""Build downloadable content packs (e.g. `ja.zip`, `common.zip`) from the
repository source tree.

Each pack is a top-level directory (`ja/`, `common/`, ...) at the repo root.
The resulting ZIP nests every file under a root entry matching the pack's
directory name and adds a `<root>/manifest.json` describing the pack version,
its required top-level directories, and a sha256/size for every file — so
clients can verify downloads and detect missing content.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Sequence
import zipfile


# Known content packs living at the repository root, one top-level
# directory each. `requiredRoots` is always derived from whatever
# subdirectories actually exist under the pack at build time (see
# `build_pack`), so it stays accurate as content is added or removed.
PACKS: tuple[str, ...] = ("ja", "common")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _entry_name(root: str, relative: Path) -> str:
    """Return a safe ZIP entry name below the pack root."""
    parts = PurePosixPath(*relative.parts).parts
    if not parts or any(part in ("", ".", "..") for part in parts):
        raise ValueError(f"unsafe world-pack path: {relative}")
    return "/".join((root, *parts))


def build_pack(
    *,
    source: Path,
    output: Path,
    version: str,
    root: str | None = None,
    required_roots: Sequence[str] | None = None,
) -> None:
    source = Path(source).resolve()
    output = Path(output)
    if not source.is_dir():
        raise ValueError(f"world-pack source is not a directory: {source}")

    root = root or source.name
    if required_roots is None:
        required_roots = sorted(
            entry.name for entry in source.iterdir() if entry.is_dir()
        )

    files: dict[str, dict[str, int | str]] = {}
    payloads: list[tuple[str, bytes]] = []
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symlinks are not allowed in world pack: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        entry = _entry_name(root, relative)
        data = path.read_bytes()
        relative_key = PurePosixPath(*relative.parts).as_posix()
        files[relative_key] = {"sha256": _sha256(data), "bytes": len(data)}
        payloads.append((entry, data))

    manifest = {
        "version": version,
        "requiredRoots": list(required_roots),
        "files": files,
    }
    manifest_bytes = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for entry, data in payloads:
            archive.writestr(entry, data)
        archive.writestr(f"{root}/manifest.json", manifest_bytes)


def _parse_required_roots(value: str | None) -> tuple[str, ...] | None:
    if value is None:
        return None
    return tuple(part.strip() for part in value.split(",") if part.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pack",
        choices=sorted(PACKS),
        help=(
            "Build a known content pack from its top-level directory "
            "(e.g. `ja` reads from ./ja, `common` reads from ./common)."
        ),
    )
    parser.add_argument(
        "--source",
        type=Path,
        help="Path to the pack source tree. Defaults to ./<pack> when --pack is set.",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument(
        "--root",
        help="ZIP root / manifest namespace. Defaults to the source directory name.",
    )
    parser.add_argument(
        "--required-roots",
        help=(
            "Comma separated override for the manifest's requiredRoots list. "
            "Defaults to the source tree's current top-level directories."
        ),
    )
    args = parser.parse_args()

    source = args.source or (Path(args.pack) if args.pack else None)
    if source is None:
        parser.error("either --pack or --source is required")

    build_pack(
        source=source,
        output=args.output,
        version=args.version,
        root=args.root,
        required_roots=_parse_required_roots(args.required_roots),
    )


if __name__ == "__main__":
    main()
