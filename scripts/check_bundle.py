"""Inspect the executable archive for tools, EJS, licenses and unexpected cookies."""
import os
import argparse
from pathlib import Path
from PyInstaller.archive.readers import CArchiveReader

root = Path(__file__).resolve().parents[1]
folder = "baixarMusicaYouTube" if os.name == "nt" else "baixarMusicaYouTubeLinux"
filename = "baixar_musica_qt.exe" if os.name == "nt" else "baixar_musica_qt"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--executable", type=Path, default=root / folder / "dist" / filename)
args = parser.parse_args()
archive = CArchiveReader(str(args.executable))
names = {name.replace("\\", "/") for name in archive.toc}
suffix = ".exe" if os.name == "nt" else ""
required = ["bin/" + name + suffix for name in ("ffmpeg", "ffprobe", "deno")]
required += ["yt_dlp_ejs/yt/solver/core.min.js", "yt_dlp_ejs/yt/solver/lib.min.js", "licenses/LICENSE", "licenses/THIRD_PARTY_NOTICES.md"]
for name in required:
    if name not in names:
        raise SystemExit("Missing resource: " + name)
if any("cookies" in name.lower() and not name.endswith((".py", ".pyc")) for name in names):
    raise SystemExit("Unexpected cookie resource in executable")
pyz_name = next(name for name in archive.toc if name.lower().endswith(".pyz"))
modules = archive.open_embedded_archive(pyz_name).toc
if "yt_dlp_ejs.yt.solver" not in modules:
    raise SystemExit("Missing importable EJS solver package")
for name in ("yt_dlp.postprocessor.embedthumbnail", "yt_dlp.postprocessor.ffmpeg", "mutagen.mp4"):
    if name not in modules:
        raise SystemExit("Missing cover artwork module: " + name)
if not any(name.startswith("PySide6/QtNetwork.") for name in names):
    raise SystemExit("Missing QtNetwork module for optional thumbnails")
if not any("/tls/" in name and ("qopensslbackend" in name or "qschannelbackend" in name) for name in names):
    raise SystemExit("Missing Qt HTTPS backend for optional thumbnails")
if os.name == "nt" and any(name.lower() in {"icuuc.dll", "ucrtbase.dll"} for name in names):
    raise SystemExit("Unexpected bundled Windows system DLL; rebuild with isolated PATH and --clean")
print("BUNDLE_OK: FFmpeg, FFprobe, Deno, EJS, cover artwork, QtNetwork/TLS, licenses; no cookie resource")
