"""Real local transfers: single selection, all, duplicate titles, partial failure."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import threading

ROOT = Path(__file__).resolve().parents[1]

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_): pass

def main():
    os.environ.pop("UIFOR_YTDLP_COOKIES", None)
    folder = "baixarMusicaYouTube" if os.name == "nt" else "baixarMusicaYouTubeLinux"
    spec = importlib.util.spec_from_file_location("post_app", ROOT / folder / "baixar_musica_qt.py")
    app = importlib.util.module_from_spec(spec); spec.loader.exec_module(app)
    fixture = ROOT / "work/validation" / ("windows" if os.name == "nt" else "linux")
    if not (fixture / "source.mp4").is_file():
        raise SystemExit("Run scripts/validate_media.py first.")
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(fixture)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    results = []
    try:
        for label, selection, missing in [("second", 2, False), ("all", None, False), ("partial", None, True)]:
            output = ROOT / "work/validation/posts" / label
            # Never recursively remove a computed directory: only own fixture outputs.
            output.mkdir(parents=True, exist_ok=True)
            for file in output.glob("fixture-*.mp4"):
                file.unlink()
            entries = [{"id": "fixture-" + str(n), "title": "Same title", "ext": "mp4",
                        "url": f"http://127.0.0.1:{server.server_port}/" + ("missing.mp4" if missing and n == 2 else "source.mp4")}
                       for n in range(1, 4)]
            metadata = {"url": "https://instagram.com/p/ABC/", "videos": [{"index": n, "id": e["id"]} for n, e in enumerate(entries, 1)]}
            opts = app.criar_opcoes_download("mp4", output, None, False, post_metadata=metadata, selected_video=selection)
            opts.update(quiet=True, no_warnings=True, noprogress=True, overwrites=True, retries=0)
            with app.YoutubeDL(opts) as downloader:
                downloader.process_ie_result({"_type": "playlist", "id": "post-fixture", "title": "Post", "extractor": "instagram", "extractor_key": "Instagram", "webpage_url": metadata["url"], "entries": entries}, download=True)
                code = downloader._download_retcode
            files = sorted(output.glob("*.mp4"))
            expected = 1 if selection is not None else 2 if missing else 3
            assert len(files) == expected, (label, files)
            if selection == 2: assert files[0].name.startswith("fixture-2-2-"), files
            assert len({p.name for p in files}) == expected
            assert (code != 0) == missing, (label, code)
            results.append({"case": label, "saved": len(files), "partial": code != 0, "unique_names": True})
        print(json.dumps(results))
        (ROOT / "work/validation/posts/results.json").write_text(json.dumps(results, indent=2) + "\n")
    finally:
        server.shutdown(); server.server_close()

if __name__ == "__main__": main()
