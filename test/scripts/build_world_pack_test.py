import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.build_world_pack import PACKS, build_pack

REPO_ROOT = Path(__file__).resolve().parents[2]


class BuildWorldPackTest(unittest.TestCase):
    def test_pack_builder_writes_ja_root_and_hash_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "assets" / "ja"
            (source / "images").mkdir(parents=True)
            (source / "content").mkdir()
            (source / "images" / "town.png").write_bytes(b"png")
            (source / "content" / "missions.json").write_text("{}")

            output = root / "world.zip"
            build_pack(source=source, output=output, version="test-1")

            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                manifest = json.loads(archive.read("ja/manifest.json"))

            self.assertTrue(
                {
                    "ja/images/town.png",
                    "ja/content/missions.json",
                    "ja/manifest.json",
                }
                <= names
            )
            self.assertEqual(manifest["version"], "test-1")
            self.assertEqual(
                manifest["files"]["images/town.png"]["sha256"],
                hashlib.sha256(b"png").hexdigest(),
            )

    def test_pack_builder_rejects_path_outside_source_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "assets" / "ja"
            (source / "images").mkdir(parents=True)
            outside = root / "outside.txt"
            outside.write_text("not part of the pack")
            (source / "images" / "escape.txt").symlink_to(outside)

            with self.assertRaises(ValueError):
                build_pack(
                    source=source,
                    output=root / "world.zip",
                    version="test-1",
                )

    def test_pack_builder_infers_root_and_required_roots_from_source_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "common"
            (source / "icons").mkdir(parents=True)
            (source / "icons" / "logo.png").write_bytes(b"png")

            output = root / "common.zip"
            build_pack(source=source, output=output, version="test-1")

            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                manifest = json.loads(archive.read("common/manifest.json"))

            self.assertIn("common/icons/logo.png", names)
            self.assertEqual(manifest["requiredRoots"], ["icons"])

    def test_pack_builder_accepts_root_and_required_roots_overrides(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "any-dir"
            (source / "images").mkdir(parents=True)
            (source / "images" / "town.png").write_bytes(b"png")

            output = root / "ja.zip"
            build_pack(
                source=source,
                output=output,
                version="test-1",
                root="ja",
                required_roots=("images", "audio"),
            )

            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                manifest = json.loads(archive.read("ja/manifest.json"))

            self.assertIn("ja/images/town.png", names)
            self.assertEqual(manifest["requiredRoots"], ["images", "audio"])

    def test_known_packs_match_repository_top_level_directories(self):
        for pack_name in PACKS:
            self.assertTrue((REPO_ROOT / pack_name).is_dir())

    def test_cli_pack_shorthand_builds_zip_from_repo_root(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "ja.zip"
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "scripts.build_world_pack",
                    "--pack",
                    "ja",
                    "--output",
                    str(output),
                    "--version",
                    "cli-test",
                ],
                cwd=REPO_ROOT,
                check=True,
            )

            self.assertTrue(output.is_file())
            with zipfile.ZipFile(output) as archive:
                manifest = json.loads(archive.read("ja/manifest.json"))
            self.assertEqual(manifest["version"], "cli-test")
            self.assertEqual(list(manifest["requiredRoots"]), list(PACKS["ja"]))


if __name__ == "__main__":
    unittest.main()
