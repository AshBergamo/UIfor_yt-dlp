"""Check native tools and bundled EJS without starting Android."""
import argparse
from io import BytesIO
import json
from pathlib import Path
import re
from zipfile import ZipFile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("apk", type=Path)
args = parser.parse_args()
with ZipFile(args.apk) as bundle:
    names = set(bundle.namelist())
    for notice in ("assets/licenses/LICENSE", "assets/licenses/THIRD_PARTY_NOTICES.md"):
        if notice not in names:
            raise SystemExit("Missing license notice: " + notice)
    abis = ("arm64-v8a", "armeabi-v7a", "x86", "x86_64")
    for abi in abis:
        for tool in ("libffmpeg.so", "libffprobe.so", "libpython.so", "libpython.zip.so", "libqjs.so"):
            entry = f"lib/{abi}/{tool}"
            if entry not in names:
                raise SystemExit("Missing native tool: " + entry)
    if any("cookies" in n.lower() or n.endswith((".jks", ".keystore")) for n in names):
        raise SystemExit("Unexpected cookie or signing file in APK")
    with ZipFile(BytesIO(bundle.read("res/raw/ytdlp"))) as backend:
        version_source = backend.read("yt_dlp/version.py").decode()
        version = re.search(r"__version__\s*=\s*['\"]([^'\"]+)", version_source).group(1)
        for required in ("yt_dlp_ejs/yt/solver/core.min.js", "yt_dlp_ejs/yt/solver/lib.min.js"):
            if required not in backend.namelist():
                raise SystemExit("Missing EJS resource: " + required)
print(json.dumps({"apk_bytes": args.apk.stat().st_size, "abis": abis, "bundled_yt_dlp": version, "ejs_present": True}))
