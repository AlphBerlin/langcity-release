import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.build_world_pack import build_pack


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


if __name__ == "__main__":
    unittest.main()
