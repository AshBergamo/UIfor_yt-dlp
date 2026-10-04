from pathlib import Path
import tarfile
import tempfile
import unittest

from scripts.package_linux import PACKAGE_NAME, TOOL_NOTICES, _safe_name, package_linux


class LinuxPackageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)
        self.project = self.repo / "linux"
        self.licenses = self.project / "bin" / "licenses"
        self.licenses.mkdir(parents=True)
        self.executable = self.project / "dist" / "baixar_musica_qt"
        self.executable.parent.mkdir()
        self.executable.write_bytes(b"\x7fELF\x02\x01\x01" + b"\x00" * 11 + b"\x3e\x00" + b"fixture")
        for name in ("install_linux.sh", "README_LINUX.md", "pixil-frame-0.png"):
            (self.project / name).write_text("fixture", encoding="utf-8")
        for name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
            (self.repo / name).write_text("fixture", encoding="utf-8")
        for name in TOOL_NOTICES:
            (self.licenses / name).write_text("fixture", encoding="utf-8")
        (self.licenses / "tools-versions.json").write_text('{}', encoding="utf-8")
        self.output = self.repo / "outputs" / (PACKAGE_NAME + ".tar.gz")

    def test_contents_permissions_and_allowlist(self):
        (self.project / "cookies.txt").write_text("must not be included", encoding="utf-8")
        nested = self.licenses / "upstream"
        nested.mkdir()
        (nested / "COPYING").write_text("nested notice", encoding="utf-8")
        package_linux(self.executable, self.output, self.project)
        with tarfile.open(self.output, "r:gz") as archive:
            entries = {entry.name: entry for entry in archive.getmembers()}
            names = {"baixar_musica_qt", "install_linux.sh", "README_LINUX.md", "pixil-frame-0.png",
                     "LICENSE", "THIRD_PARTY_NOTICES.md", "licenses/upstream/COPYING"}
            names.update("licenses/" + name for name in TOOL_NOTICES)
            self.assertEqual(set(entries), {PACKAGE_NAME + "/" + name for name in names})
            for name, entry in entries.items():
                self.assertTrue(entry.isfile())
                self.assertEqual(entry.mode, 0o755 if name.endswith(("/baixar_musica_qt", "/install_linux.sh")) else 0o644)
                self.assertEqual((entry.uid, entry.gid, entry.uname, entry.gname), (0, 0, "", ""))
            self.assertEqual(archive.extractfile(PACKAGE_NAME + "/baixar_musica_qt").read(), self.executable.read_bytes())

    def test_rejects_wrong_platform_and_missing_required_resource(self):
        original = self.executable.read_bytes()
        self.executable.write_bytes(b"MZ" + b"\x00" * 30)
        with self.assertRaisesRegex(ValueError, "ELF64 x86_64"):
            package_linux(self.executable, self.output, self.project)
        self.executable.write_bytes(original)
        (self.project / "install_linux.sh").unlink()
        with self.assertRaises(FileNotFoundError):
            package_linux(self.executable, self.output, self.project)
        self.assertFalse(self.output.exists())
        (self.project / "install_linux.sh").write_text("fixture", encoding="utf-8")
        (self.licenses / "deno-LICENSE.txt").unlink()
        with self.assertRaises(FileNotFoundError):
            package_linux(self.executable, self.output, self.project)

    def test_rejects_sensitive_license_files_and_output_collision(self):
        package_linux(self.executable, self.output, self.project)
        previous_package = self.output.read_bytes()
        for name in ("cookies.txt", ".env", "release.jks", "secret.json"):
            with self.subTest(name=name):
                sensitive = self.licenses / name
                sensitive.write_text("fixture", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "cannot be packaged"):
                    package_linux(self.executable, self.output, self.project)
                self.assertEqual(self.output.read_bytes(), previous_package)
                sensitive.unlink()
        original = self.executable.read_bytes()
        with self.assertRaisesRegex(ValueError, "must not overwrite"):
            package_linux(self.executable, self.executable, self.project)
        self.assertEqual(self.executable.read_bytes(), original)
        with self.assertRaisesRegex(ValueError, "outside bin/licenses"):
            package_linux(self.executable, self.licenses / "package.tar.gz", self.project)

    def test_rejects_symbolic_link_in_license_tree(self):
        link = self.licenses / "COPYING"
        try:
            link.symlink_to(self.repo / "LICENSE")
        except OSError as error:
            self.skipTest(f"Host cannot create symbolic links: {error}")
        with self.assertRaisesRegex(ValueError, "symbolic links"):
            package_linux(self.executable, self.output, self.project)

    def test_rejects_unsafe_archive_paths(self):
        for name in ("/absolute", "licenses/../outside", "licenses\\outside"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "Unsafe archive path"):
                _safe_name(name)

    def test_rejects_windows_tool_notices(self):
        (self.licenses / "tools-versions.json").write_text('{"ffmpeg_archive_sha256": "fixture"}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Windows FFmpeg notices"):
            package_linux(self.executable, self.output, self.project)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
