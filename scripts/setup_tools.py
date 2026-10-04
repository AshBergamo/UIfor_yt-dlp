"""Fetch verified desktop tools into an ignored bin/ directory, without admin install."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile


def read_url(url):
    request = urllib.request.Request(url, headers={"User-Agent": "UIfor_yt-dlp-build"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def download(url, path, expected):
    if not expected or len(expected) != 64:
        raise RuntimeError("No SHA256 available for " + path.name)
    request = urllib.request.Request(url, headers={"User-Agent": "UIfor_yt-dlp-build"})
    digest = hashlib.sha256()
    with urllib.request.urlopen(request, timeout=60) as response, path.open("wb") as out:
        while chunk := response.read(1024 * 1024):
            out.write(chunk)
            digest.update(chunk)
    if digest.hexdigest().lower() != expected.lower():
        raise RuntimeError("SHA256 mismatch: " + path.name)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--system-ffmpeg", action="store_true", help="Use the ffmpeg/ffprobe pair on PATH (Linux)")
    args = parser.parse_args()
    destination = args.output_dir.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    licenses = destination / "licenses"
    licenses.mkdir(exist_ok=True)
    versions = {}
    windows = platform.system() == "Windows"
    if platform.machine().lower() not in {"amd64", "x86_64"}:
        raise RuntimeError("This tool bootstrap currently supports x86_64 only.")
    with tempfile.TemporaryDirectory(prefix="uifor-tools-") as tmp:
        tmp = Path(tmp)
        if args.system_ffmpeg:
            for tool in ("ffmpeg", "ffprobe"):
                source = shutil.which(tool)
                if not source:
                    raise RuntimeError(tool + " is not on PATH")
                shutil.copy2(source, destination / Path(source).name)
            licenses.joinpath("ffmpeg-source.txt").write_text(
                "System ffmpeg/ffprobe: consult your distribution's package source and copyright files.\nhttps://ffmpeg.org/legal.html\n", encoding="utf-8")
            for copyright_file in (Path("/usr/share/doc/ffmpeg/copyright"),):
                if copyright_file.is_file():
                    shutil.copy2(copyright_file, licenses / "ffmpeg-copyright.txt")
        elif windows:
            base = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
            expected = read_url(base + ".sha256").decode().split()[0]
            archive = tmp / "ffmpeg.zip"
            versions["ffmpeg_archive_sha256"] = download(base, archive, expected)
            with zipfile.ZipFile(archive) as bundle:
                for tool in ("ffmpeg.exe", "ffprobe.exe"):
                    name = next(n for n in bundle.namelist() if n.endswith("/bin/" + tool))
                    destination.joinpath(tool).write_bytes(bundle.read(name))
                for name in bundle.namelist():
                    if Path(name).name.upper().startswith(("LICENSE", "COPYING", "README")) and not name.endswith("/"):
                        licenses.joinpath("ffmpeg-" + Path(name).name).write_bytes(bundle.read(name))
            licenses.joinpath("ffmpeg-source.txt").write_text(
                "Builds/configuration/source: https://www.gyan.dev/ffmpeg/builds/\nUpstream source: https://ffmpeg.org/download.html\n", encoding="utf-8")
        else:
            raise RuntimeError("On Linux use --system-ffmpeg after installing ffmpeg/ffprobe.")

        release = json.loads(read_url("https://api.github.com/repos/denoland/deno/releases/latest"))
        target = "deno-x86_64-pc-windows-msvc.zip" if windows else "deno-x86_64-unknown-linux-gnu.zip"
        asset = next(a for a in release["assets"] if a["name"] == target)
        expected = (asset.get("digest") or "").removeprefix("sha256:")
        if not expected:
            expected = read_url(asset["browser_download_url"] + ".sha256sum").decode().split()[0]
        archive = tmp / "deno.zip"
        versions["deno_archive_sha256"] = download(asset["browser_download_url"], archive, expected)
        filename = "deno.exe" if windows else "deno"
        with zipfile.ZipFile(archive) as bundle:
            destination.joinpath(filename).write_bytes(bundle.read(filename))
        destination.joinpath(filename).chmod(0o755)
        licenses.joinpath("deno-LICENSE.txt").write_bytes(read_url(
            f"https://raw.githubusercontent.com/denoland/deno/{release['tag_name']}/LICENSE.md"))
        versions["deno_source"] = f"https://github.com/denoland/deno/tree/{release['tag_name']}"

    for tool in ("ffmpeg", "ffprobe", "deno"):
        executable = destination / (tool + ".exe" if windows else tool)
        flag = "--version" if tool == "deno" else "-version"
        versions[tool] = subprocess.check_output([str(executable), flag], text=True, encoding="utf-8").splitlines()[0]
    licenses.joinpath("tools-versions.json").write_text(json.dumps(versions, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(versions, indent=2))


if __name__ == "__main__":
    main()
