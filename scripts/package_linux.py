"""Package a checked Linux PyInstaller executable and its user installer."""
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "UIfor_yt-dlp-v3.3-linux-x86_64"
TOOL_NOTICES = ("ffmpeg-source.txt", "deno-LICENSE.txt", "tools-versions.json")


def _regular_file(path):
    if path.is_symlink():
        raise ValueError(f"Package resources must not be symbolic links: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"Missing package resource: {path}")


def _safe_name(name):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name:
        raise ValueError(f"Unsafe archive path: {name}")
    for part in path.parts:
        lower = part.lower()
        if (lower.startswith(".env") or any(word in lower for word in ("cookie", "secret", "password", "token"))
                or lower in {"release-signing", "keystore.properties"}
                or Path(lower).suffix in {".jks", ".keystore", ".p12", ".pfx", ".pem", ".key"}):
            raise ValueError(f"Authentication/signing material cannot be packaged: {name}")


def package_linux(executable, output, project_dir):
    """Build the archive from an explicit allowlist; never stage/delete a tree."""
    executable, output, project_dir = Path(executable), Path(output), Path(project_dir)
    _regular_file(executable)
    with executable.open("rb") as source:
        header = source.read(20)
    if len(header) < 20 or header[:7] != b"\x7fELF\x02\x01\x01" or header[18:20] != b"\x3e\x00":
        raise ValueError("The executable must be a Linux ELF64 x86_64 build.")

    files = {"baixar_musica_qt": executable}
    files.update({name: project_dir / name for name in ("install_linux.sh", "README_LINUX.md", "pixil-frame-0.png")})
    files.update({name: project_dir.parent / name for name in ("LICENSE", "THIRD_PARTY_NOTICES.md")})
    licenses = project_dir / "bin" / "licenses"
    if licenses.is_symlink() or not licenses.is_dir():
        raise ValueError("Missing regular bin/licenses directory; run scripts/setup_tools.py.")
    for name in TOOL_NOTICES:
        _regular_file(licenses / name)
    versions = json.loads((licenses / "tools-versions.json").read_text(encoding="utf-8"))
    if "ffmpeg_archive_sha256" in versions:
        raise ValueError("Windows FFmpeg notices cannot be used for a Linux package; prepare Linux bin/licenses.")
    for path in sorted(licenses.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Package resources must not be symbolic links: {path}")
        if not path.is_dir():
            files["licenses/" + path.relative_to(licenses).as_posix()] = path
    for name, source in files.items():
        _safe_name(name)
        _regular_file(source)
        if output.resolve() == source.resolve():
            raise ValueError("The archive output must not overwrite a package resource.")
    if output.resolve().is_relative_to(licenses.resolve()):
        raise ValueError("The archive output must be outside bin/licenses.")

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=output.name + ".", suffix=".tmp", dir=output.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with tarfile.open(temporary_path, "w:gz") as archive:
            for name, source in files.items():
                entry = archive.gettarinfo(str(source), PACKAGE_NAME + "/" + name)
                entry.mode = 0o755 if name in {"baixar_musica_qt", "install_linux.sh"} else 0o644
                entry.uid = entry.gid = 0
                entry.uname = entry.gname = ""
                with source.open("rb") as contents:
                    archive.addfile(entry, contents)
        with tarfile.open(temporary_path, "r:gz") as archive:
            entries = archive.getmembers()
            expected = {PACKAGE_NAME + "/" + name: 0o755 if name in {"baixar_musica_qt", "install_linux.sh"} else 0o644
                        for name in files}
            if len(entries) != len(expected) or {entry.name for entry in entries} != set(expected):
                raise ValueError("The package resource list did not match its allowlist.")
            for entry in entries:
                _safe_name(entry.name)
                if not entry.isfile() or entry.mode != expected[entry.name]:
                    raise ValueError(f"Invalid package entry or permissions: {entry.name}")
        os.replace(temporary_path, output)
    finally:
        temporary_path.unlink(missing_ok=True)
    return output.resolve()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", type=Path, default=ROOT / "baixarMusicaYouTubeLinux/dist/baixar_musica_qt")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs")
    args = parser.parse_args()
    output = package_linux(args.executable, args.output_dir / (PACKAGE_NAME + ".tar.gz"), ROOT / "baixarMusicaYouTubeLinux")
    print(f"LINUX_PACKAGE_OK: {output} ({output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
