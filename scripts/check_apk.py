"""Check native tools and bundled EJS without starting Android."""
import argparse
from io import BytesIO
import json
from pathlib import Path
import re
from zipfile import BadZipFile, ZipFile

MAX_BACKEND_RESOURCE_BYTES = 32 * 1024 * 1024


def read_backend(bundle):
    """Find the backend when release AAPT has shortened its resource path."""
    if "res/raw/ytdlp" in bundle.namelist():
        with bundle.open("res/raw/ytdlp") as resource:
            payload = resource.read(MAX_BACKEND_RESOURCE_BYTES + 1)
        if len(payload) > MAX_BACKEND_RESOURCE_BYTES:
            raise SystemExit("Bundled yt-dlp resource exceeds inspector size limit")
        return payload

    found = None
    for entry in bundle.infolist():
        if not entry.filename.startswith("res/") or entry.is_dir():
            continue
        with bundle.open(entry) as resource:
            header = resource.read(min(256, MAX_BACKEND_RESOURCE_BYTES + 1))
            zip_start = b"PK\x03\x04"
            # yt-dlp's zipapp includes a short Python shebang before the ZIP.
            if not (header.startswith(zip_start)
                    or header.startswith(b"#!") and header.partition(b"\n")[2].startswith(zip_start)):
                continue
            if entry.file_size > MAX_BACKEND_RESOURCE_BYTES:
                raise SystemExit("ZIP resource exceeds inspector size limit: " + entry.filename)
            payload = header + resource.read(MAX_BACKEND_RESOURCE_BYTES - len(header) + 1)
        if len(payload) > MAX_BACKEND_RESOURCE_BYTES:
            raise SystemExit("ZIP resource exceeds inspector size limit: " + entry.filename)
        try:
            with ZipFile(BytesIO(payload)) as candidate:
                if "yt_dlp/version.py" not in candidate.namelist():
                    continue
        except BadZipFile:
            continue
        if found is not None:
            raise SystemExit("Ambiguous bundled yt-dlp resources in APK")
        found = payload
    if found is None:
        raise SystemExit("Missing bundled yt-dlp resource in APK")
    return found


def inspect_apk(apk):
    with ZipFile(apk) as bundle:
        names = set(bundle.namelist())
        for notice in ("assets/sources.json", "assets/licenses/LICENSE", "assets/licenses/THIRD_PARTY_NOTICES.md"):
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
        with ZipFile(BytesIO(read_backend(bundle))) as backend:
            version_source = backend.read("yt_dlp/version.py").decode()
            version = re.search(r"__version__\s*=\s*['\"]([^'\"]+)", version_source).group(1)
            for required in ("yt_dlp_ejs/yt/solver/core.min.js", "yt_dlp_ejs/yt/solver/lib.min.js"):
                if required not in backend.namelist():
                    raise SystemExit("Missing EJS resource: " + required)
            for site in ("youtube", "instagram", "twitter", "facebook", "tiktok", "twitch"):
                if f"yt_dlp/extractor/{site}.py" not in backend.namelist() and f"yt_dlp/extractor/{site}/__init__.py" not in backend.namelist():
                    raise SystemExit("Missing source extractor: " + site)
        catalog = json.loads(bundle.read("assets/sources.json"))
        if {source["id"] for source in catalog["sources"]} != {"youtube", "instagram", "twitter", "facebook", "tiktok", "twitch"}:
            raise SystemExit("Unexpected source catalog")
    return {"apk_bytes": apk.stat().st_size, "abis": abis, "bundled_yt_dlp": version, "ejs_present": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect_apk(args.apk)))


if __name__ == "__main__":
    main()
