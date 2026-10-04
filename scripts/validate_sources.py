"""Opt-in public network smoke, with 3-second ranges and no personal cookies."""
import argparse
import concurrent.futures
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = {
    "youtube": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
    "tiktok": "https://www.tiktok.com/@pokemonlife22/video/7059698374567611694",
    "instagram": "https://www.instagram.com/reel/Chunk8-jurw/",
    "twitter": "https://twitter.com/captainamerica/status/719944021058060289",
    "facebook": "https://www.facebook.com/reel/1591316522498163",
    "twitch": "https://clips.twitch.tv/FaintLightGullWholeWheat",
}

def child(site, full=False, url=None, item=None):
    os.environ.pop("UIFOR_YTDLP_COOKIES", None)
    folder = "baixarMusicaYouTube" if os.name == "nt" else "baixarMusicaYouTubeLinux"
    spec = importlib.util.spec_from_file_location("source_validation_app", ROOT / folder / "baixar_musica_qt.py")
    app = importlib.util.module_from_spec(spec); spec.loader.exec_module(app)
    from media_sources import lookup_metadata, friendly_error, SilentLogger
    result = {"source": site, "metadata": False, "download": False, "mode": "full" if full else "3-second-range"}
    stage = "metadata"
    try:
        metadata = lookup_metadata(url or SAMPLES[site], app.opcoes_base(silencioso=True, cookies=False))
        result.update(metadata=True, videos=len(metadata["videos"]))
        case = ("full" if full else "range") + "-" + str(item or "all") + "-" + hashlib.sha256(metadata["url"].encode()).hexdigest()[:8]
        output = ROOT / "work/validation/public-sources" / site / case
        output.mkdir(parents=True, exist_ok=True)
        options = app.criar_opcoes_download("mp4", output, None, False,
                    post_metadata=metadata if site != "youtube" else None, selected_video=item)
        options.update(quiet=True, logger=SilentLogger(), no_warnings=True, noprogress=True,
                       socket_timeout=8, retries=0, extractor_retries=0, fragment_retries=0, overwrites=True)
        if not full:
            options["download_ranges"] = app.download_range_func([], [(0, 3)])
        stage = "download"
        with app.YoutubeDL(options) as downloader:
            code = downloader.download([metadata["url"]])
        if code: raise RuntimeError("A transferência não foi concluída.")
        files = list(output.glob("*.mp4"))
        if not files: raise RuntimeError("Nenhum MP4 final encontrado.")
        probes = []
        for file in files:
            data = json.loads(subprocess.check_output([str(app.caminho_ferramenta("ffprobe")), "-v", "error",
                           "-show_streams", "-show_format", "-of", "json", str(file)], text=True, encoding="utf-8"))
            if not any(s["codec_type"] == "video" and not s.get("disposition", {}).get("attached_pic") for s in data["streams"]):
                raise RuntimeError("O arquivo não contém vídeo.")
            probes.append({"bytes": file.stat().st_size, "duration": float(data["format"]["duration"]),
                           "cover": any(s.get("disposition", {}).get("attached_pic") for s in data["streams"])})
        result.update(download=True, files=probes)
    except Exception as error:
        result.update(stage=stage, error=friendly_error(error, site))
    print(json.dumps(result, ensure_ascii=True), flush=True)

def run(site, full, url=None, item=None):
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", "--site", site]
    if full: command.append("--full")
    if url: command.extend(["--url", url])
    if item is not None: command.extend(["--item", str(item)])
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                               encoding="utf-8", errors="replace", start_new_session=os.name != "nt")
    try:
        output, _ = process.communicate(timeout=90 if full else 60)
        for line in reversed(output.splitlines()):
            if line.startswith("{"): return json.loads(line)
        return {"source": site, "download": False, "stage": "process", "error": "Smoke process did not return results."}
    except subprocess.TimeoutExpired:
        # Only the process created here and its own children; never a user's app.
        if os.name == "nt": subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
        else: os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        return {"source": site, "download": False, "stage": "timeout", "error": "Public smoke exceeded its time limit."}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--network", action="store_true")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--site", choices=["all", *SAMPLES], default="all")
    parser.add_argument("--full", action="store_true", help="Download the whole sample instead of a 3-second range")
    parser.add_argument("--url", help="Alternate public sample URL for the selected site")
    parser.add_argument("--item", type=int, help="Extractor index of one video in the post")
    args = parser.parse_args()
    if args.url and args.site == "all": parser.error("--url requires --site")
    if args.worker:
        child(args.site, args.full, args.url, args.item); return
    if not args.network:
        parser.error("Use --network to authorize public requests; this check is excluded from CI.")
    sites = list(SAMPLES) if args.site == "all" else [args.site]
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(lambda site: run(site, args.full, args.url, args.item), sites):
            results.append(result); print(json.dumps(result, ensure_ascii=True), flush=True)
    output = ROOT / "work/validation/public-sources"
    output.mkdir(parents=True, exist_ok=True)
    (output / (args.site + ("-custom" if args.url else "") + ("-item" + str(args.item) if args.item else "") + ("-full" if args.full else "") + "-results.json")).write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    if any(not r.get("download") and r["source"] != "tiktok" for r in results): raise SystemExit(1)

if __name__ == "__main__": main()
