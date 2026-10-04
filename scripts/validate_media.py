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


def stream_hashes(ffmpeg, path):
    """Compare encoded video/audio packets, excluding attached artwork."""
    output = subprocess.check_output([
        ffmpeg, "-v", "error", "-i", str(path), "-map", "0:v:0", "-map", "0:a:0",
        "-c", "copy", "-f", "streamhash", "-hash", "sha256", "-",
    ], text=True)
    return output.strip().splitlines()


def validate_covers(app, work, server, ffmpeg, ffprobe):
    source_hashes = stream_hashes(ffmpeg, work / "source.mp4")
    results = []
    for kind, image in [("mp4", "cover.jpg"), ("mp4", "cover.webp"),
                        ("mkv", "cover.jpg"), ("mkv", "cover.webp"),
                        ("mp4", "missing.jpg"), ("mkv", None)]:
        output = work / f"cover-{kind}-{image or 'absent'}"
        output.mkdir(exist_ok=True)
        options = app.criar_opcoes_download(kind, output, None, False)
        options.update(quiet=True, noprogress=True, overwrites=True)
        info = {"id": "cover-fixture", "title": "Cover fixture", "ext": "mp4",
                "url": f"http://127.0.0.1:{server.server_port}/source.mp4"}
        if image:
            info["thumbnail"] = f"http://127.0.0.1:{server.server_port}/{image}"
        with app.YoutubeDL(options) as downloader:
            downloader.process_ie_result(info, download=True)
        files = list(output.iterdir())
        assert len(files) == 1 and files[0].suffix == f".{kind}", files
        final = files[0]
        assert stream_hashes(ffmpeg, final) == source_hashes, f"{kind}: media changed"
        data = json.loads(subprocess.check_output([
            ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(final),
        ], text=True))
        covers = [s for s in data["streams"] if s.get("disposition", {}).get("attached_pic") == 1]
        expected = image in {"cover.jpg", "cover.webp"}
        assert bool(covers) == expected, (kind, image, data)
        if expected:
            assert len(covers) == 1 and covers[0]["codec_name"] == "mjpeg", covers
            if kind == "mp4" and image == "cover.jpg":
                from mutagen.mp4 import MP4
                assert bytes(MP4(final)["covr"][0]) == (work / image).read_bytes()
        duration = float(data["format"]["duration"])
        assert 5.8 <= duration <= 6.4, duration
        result = {"format": kind, "thumbnail": image, "cover_embedded": bool(covers),
                  "video_audio_unchanged": True, "sidecars": False, "duration": duration}
        results.append(result)
        print(json.dumps(result), flush=True)
    (work / "cover-results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")


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
    for ext in ("jpg", "webp"):
        subprocess.run([ffmpeg, "-v", "error", "-y", "-f", "lavfi", "-i",
                        "color=c=red:s=640x360", "-frames:v", "1", str(work / f"cover.{ext}")], check=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(work)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    results = []
    try:
        for kind, source, label in [(k, "source.webm" if k == "webm" else "source.mp4", k)
                                    for k in ("mp4", "mp3", "webm", "mkv", "gif", "wav")] + [("webm", "source.mp4", "webm-from-mp4")]:
            output = work / label
            output.mkdir(exist_ok=True)
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
            if kind == "webm":
                assert "webm" in data["format"]["format_name"], data
                assert {st["codec_name"] for st in data["streams"]} == {"vp9", "opus"}, data
            result = {"input": source, "format": kind, "duration": duration, "streams": sorted(streams), "bytes": files[0].stat().st_size}
            results.append(result)
            print(json.dumps(result), flush=True)
        validate_covers(app, work, server, ffmpeg, ffprobe)
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
