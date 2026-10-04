from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from scripts.check_apk import inspect_apk, read_backend


class ApkInspectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.apk = Path(temporary.name) / "fixture.apk"
        self.entries = {
            "assets/sources.json": json.dumps({"sources": [{"id": site} for site in
                ("youtube", "instagram", "twitter", "facebook", "tiktok", "twitch")]}).encode(),
            "assets/licenses/LICENSE": b"fixture",
            "assets/licenses/THIRD_PARTY_NOTICES.md": b"fixture",
            "res/icon.png": b"image fixture",
        }
        for abi in ("arm64-v8a", "armeabi-v7a", "x86", "x86_64"):
            for tool in ("libffmpeg.so", "libffprobe.so", "libpython.so", "libpython.zip.so", "libqjs.so"):
                self.entries[f"lib/{abi}/{tool}"] = b"native fixture"

    def backend(self, missing=None):
        contents = {
            "yt_dlp/version.py": b"__version__ = '2025.11.12'",
            "yt_dlp_ejs/yt/solver/core.min.js": b"fixture",
            "yt_dlp_ejs/yt/solver/lib.min.js": b"fixture",
            "yt_dlp/extractor/youtube/__init__.py": b"fixture",
        }
        for site in ("instagram", "twitter", "facebook", "tiktok", "twitch"):
            contents[f"yt_dlp/extractor/{site}.py"] = b"fixture"
        contents.pop(missing, None)
        output = BytesIO()
        with ZipFile(output, "w") as archive:
            for name, payload in contents.items():
                archive.writestr(name, payload)
        return output.getvalue()

    def write_apk(self):
        with ZipFile(self.apk, "w") as archive:
            for name, payload in self.entries.items():
                archive.writestr(name, payload)

    def test_debug_and_optimized_resource_paths(self):
        shebang = b"#!/usr/bin/env python3\n"
        for name, prefix in (("res/raw/ytdlp", shebang), ("res/Nc", b""), ("res/Nc", shebang)):
            with self.subTest(name=name, prefix=prefix):
                self.entries[name] = prefix + self.backend()
                self.write_apk()
                result = inspect_apk(self.apk)
                self.assertEqual(result["bundled_yt_dlp"], "2025.11.12")
                self.assertEqual(result["abis"], ("arm64-v8a", "armeabi-v7a", "x86", "x86_64"))
                self.assertTrue(result["ejs_present"])
                self.assertEqual(result["apk_bytes"], self.apk.stat().st_size)
                del self.entries[name]

    def test_fallback_ignores_non_backend_zip_and_invalid_zip(self):
        decoy = BytesIO()
        with ZipFile(decoy, "w") as archive:
            archive.writestr("unrelated.txt", b"fixture")
        self.entries.update({"res/decoy": decoy.getvalue(), "res/invalid": b"PK\x03\x04invalid",
                             "assets/untrusted": self.backend(), "res/Nc": self.backend()})
        self.write_apk()
        self.assertTrue(inspect_apk(self.apk)["ejs_present"])

    def test_missing_and_ambiguous_backend_are_rejected(self):
        self.write_apk()
        with self.assertRaisesRegex(SystemExit, "Missing bundled yt-dlp"):
            inspect_apk(self.apk)
        self.entries.update({"res/Nc": self.backend(), "res/other": self.backend()})
        self.write_apk()
        with self.assertRaisesRegex(SystemExit, "Ambiguous bundled yt-dlp"):
            inspect_apk(self.apk)

    def test_missing_ejs_and_extractor_are_still_rejected(self):
        for missing, message in (("yt_dlp_ejs/yt/solver/core.min.js", "Missing EJS"),
                                 ("yt_dlp_ejs/yt/solver/lib.min.js", "Missing EJS"),
                                 ("yt_dlp/extractor/youtube/__init__.py", "Missing source extractor")):
            with self.subTest(missing=missing):
                self.entries["res/Nc"] = self.backend(missing)
                self.write_apk()
                with self.assertRaisesRegex(SystemExit, message):
                    inspect_apk(self.apk)

    def test_license_native_and_sensitive_entries_remain_checked(self):
        self.entries["res/Nc"] = self.backend()
        for missing, message in (("assets/licenses/LICENSE", "Missing license notice"),
                                 ("lib/x86/libpython.zip.so", "Missing native tool")):
            with self.subTest(missing=missing):
                previous = self.entries.pop(missing)
                self.write_apk()
                with self.assertRaisesRegex(SystemExit, message):
                    inspect_apk(self.apk)
                self.entries[missing] = previous
        for sensitive in ("assets/cookies.txt", "assets/signing.jks", "assets/signing.keystore"):
            with self.subTest(sensitive=sensitive):
                self.entries[sensitive] = b"fixture"
                self.write_apk()
                with self.assertRaisesRegex(SystemExit, "Unexpected cookie or signing file"):
                    inspect_apk(self.apk)
                del self.entries[sensitive]

    def test_catalog_remains_checked(self):
        self.entries["res/Nc"] = self.backend()
        self.entries["assets/sources.json"] = b'{"sources": [{"id": "youtube"}]}'
        self.write_apk()
        with self.assertRaisesRegex(SystemExit, "Unexpected source catalog"):
            inspect_apk(self.apk)

    def test_zip_resource_reads_are_bounded(self):
        for path in ("res/Nc", "res/raw/ytdlp"):
            with self.subTest(path=path):
                self.entries[path] = self.backend()
                self.write_apk()
                with patch("scripts.check_apk.MAX_BACKEND_RESOURCE_BYTES", 64), ZipFile(self.apk) as bundle:
                    with self.assertRaisesRegex(SystemExit, "inspector size limit"):
                        read_backend(bundle)
                del self.entries[path]


if __name__ == "__main__":
    unittest.main()
