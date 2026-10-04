"""Exercise actual yt-dlp + FFmpeg conversions using generated local media."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import threading


ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--youtube", action="store_true", help="Additional short public YouTube test, without cookies")
    parser.add_argument("--youtube-url", default="https://www.youtube.com/watch?v=jNQXAC9IVRw", help="Public short test source")
    parser.add_argument("--platform", choices=["windows", "linux"], default="windows" if os.name == "nt" else "linux")
    args = parser.parse_args()
    folder = "baixarMusicaYouTube" if args.platform == "windows" else "baixarMusicaYouTubeLinux"
    spec = importlib.util.spec_from_file_location("app", ROOT / folder / "baixar_musica_qt.py")
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    os.environ.pop("UIFOR_YTDLP_COOKIES", None)
    app.verificar_dependencias()
    work = ROOT / "work" / "validation" / args.platform
    work.mkdir(parents=True, exist_ok=True)
    ffmpeg = str(app.caminho_ffmpeg())
    ffprobe = str(app.caminho_ferramenta("ffprobe"))
    common = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=15:duration=6", "-f", "lavfi", "-i", "sine=frequency=440:duration=6"]
    subprocess.run(common + ["-c:v", "libx264", "-g", "15", "-c:a", "aac", "-movflags", "+faststart", str(work / "source.mp4")], check=True)
    subprocess.run(common + ["-c:v", "libvpx-vp9", "-c:a", "libopus", str(work / "source.webm")], check=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(work)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    results = []
    try:
        for kind in ("mp4", "mp3", "webm", "mkv", "gif", "wav"):
            output = work / kind
            output.mkdir(exist_ok=True)
            source = "source.webm" if kind == "webm" else "source.mp4"
            options = app.criar_opcoes_download(kind, output, None, False, 1, 3)
            options.update(quiet=True, no_warnings=True, noprogress=True, overwrites=True)
            with app.YoutubeDL(options) as downloader:
                downloader.download([f"http://127.0.0.1:{server.server_port}/{source}"])
            files = list(output.glob("*." + kind))
            assert len(files) == 1, f"{kind}: final output missing"
            data = json.loads(subprocess.check_output([ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(files[0])], text=True))
            streams = {stream["codec_type"] for stream in data["streams"]}
            duration = float(data["format"]["duration"])
            expected_streams = {"audio"} if kind in {"mp3", "wav"} else {"video"} if kind == "gif" else {"audio", "video"}
            assert streams == expected_streams, (kind, streams)
            if kind == "gif":
                assert abs(duration - 2) <= 0.2, (kind, duration)
            else:
                assert 5.8 <= duration <= 6.4, (kind, duration)
            result = {"format": kind, "duration": duration, "streams": sorted(streams), "bytes": files[0].stat().st_size}
            results.append(result)
            print(json.dumps(result), flush=True)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
        (work / "local-results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    if args.youtube:
        options = app.criar_opcoes_download("mp4", work / "youtube", None, False)
        options.update(quiet=True, noprogress=True, socket_timeout=20, retries=1, extractor_retries=1, fragment_retries=1)
        outcome = {"cookies_used": False, "success": False}
        try:
            with app.YoutubeDL(options) as downloader:
                downloader.download([args.youtube_url])
            outcome["success"] = True
        except Exception as error:
            outcome["error"] = app.limpar_mensagem_erro(error)
        (work / "youtube-result.json").write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(outcome), flush=True)
        if not outcome["success"]:
            raise SystemExit(2)


if __name__ == "__main__":
    main()
