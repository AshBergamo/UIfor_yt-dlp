import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QObject, Signal, QTimer, QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
import media_sources as sources

ROOT = Path(__file__).resolve().parents[1]


class SourceTests(unittest.TestCase):
    def test_url_cases(self):
        for url, expected, short in json.loads((ROOT / "tests/source_cases.json").read_text()):
            with self.subTest(url=url):
                actual = sources.classify_url(url)
                self.assertEqual(actual["id"] if actual else None, expected)
                if actual:
                    self.assertEqual(actual["short"], short)

    def test_installed_extractors_and_scope(self):
        from yt_dlp import YoutubeDL
        with YoutubeDL({"allowed_extractors": sources.EXTRACTORS, "quiet": True}) as dl:
            names = {ie.IE_NAME.lower() for ie in dl._ies.values()}
        self.assertTrue({"instagram", "twitter", "facebook", "twitch:clips", "twitch:vod", "tiktok"} <= names)
        self.assertNotIn("generic", names)
        self.assertNotIn("instagram:user", names)
        self.assertNotIn("twitter:user", names)

    def test_sharing_redirects_are_bounded_and_reject_other_destinations(self):
        class Response:
            def __init__(self, location): self.headers = {"Location": location}
            def __enter__(self): return self
            def __exit__(self, *_): pass
        class Opener:
            calls = 0
            def __init__(self, target): self.target = target
            def open(self, *_args, **_kwargs):
                self.calls += 1
                return Response(self.target)
        good = Opener("https://www.tiktok.com/@name/video/123")
        self.assertEqual(sources.resolve_url("https://vm.tiktok.com/abc", good), good.target)
        bad = Opener("https://example.org/video")
        with self.assertRaises(ValueError): sources.resolve_url("https://t.co/abc", bad)
        self.assertEqual(bad.calls, 1)
        loop = Opener("https://t.co/abc")
        with self.assertRaises(ValueError): sources.resolve_url("https://t.co/abc", loop)
        self.assertEqual(loop.calls, 5)

    def test_post_indices_selection_and_live_rejection(self):
        info = {"_type": "playlist", "entries": [None,
                {"id": "a", "playlist_index": 2, "title": "Same title", "thumbnail": "https://img/a"},
                {"id": "b", "playlist_index": 4, "title": "Same title"}]}
        result = sources.project_metadata(info, "https://instagram.com/p/ABC/")
        self.assertEqual(sources.selection_options(result)["playlist_items"], "2,4")
        self.assertEqual(sources.selection_options(result, 4)["playlist_items"], "4")
        with self.assertRaises(ValueError): sources.selection_options(result, 3)
        with self.assertRaises(ValueError):
            sources.project_metadata({"is_live": True}, "https://twitch.tv/videos/123")

    def test_lookup_never_uses_personal_cookies_or_writes_media(self):
        from unittest.mock import MagicMock
        mock = MagicMock()
        mock.return_value.__enter__.return_value.extract_info.return_value = {"id": "a", "title": "Clip"}
        with patch("yt_dlp.YoutubeDL", mock):
            result = sources.lookup_metadata("https://clips.twitch.tv/ABC", {"cookiefile": "private.txt"})
        options = mock.call_args.args[0]
        self.assertNotIn("cookiefile", options)
        self.assertTrue(options["simulate"])
        self.assertFalse(options["cachedir"])
        self.assertEqual(result["videos"][0]["title"], "Clip")

    def test_errors_are_readable_and_omit_signed_urls(self):
        message = sources.friendly_error("HTTP 429 https://cdn.test/?token=private", "Instagram")
        self.assertIn("limitou", message)
        self.assertNotIn("token=private", message)


class PostUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.settings = QSettings(str(Path(directory.name) / "ui.ini"), QSettings.Format.IniFormat)

    def test_select_second_all_and_clear_on_edit(self):
        for folder in ("baixarMusicaYouTube", "baixarMusicaYouTubeLinux"):
            spec = importlib.util.spec_from_file_location("source_ui_" + folder, ROOT / folder / "baixar_musica_qt.py")
            app = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(app)
            class Lookup(QObject):
                finished = Signal(dict)
                failed = Signal(str)
                instances = []
                def __init__(self, _entry, url, _timeout, parent):
                    super().__init__(parent); self.url = url; self.cancelled = False
                    self.instances.append(self)
                def start(self): pass
                def cancel(self): self.cancelled = True
            with patch.object(app, "MetadataLookup", Lookup):
                window = app.JanelaPrincipal(self.settings)
                try:
                    window.input_url.setText("https://instagram.com/p/ABC/")
                    window._preview_timer.stop()
                    window._buscar_previa()
                    job = Lookup.instances[-1]
                    self.assertFalse(window._working)
                    job.finished.emit({"url": job.url, "source": "instagram", "videos": [
                        {"index": 1, "id": "a", "title": "First"},
                        {"index": 3, "id": "b", "title": "Second"}]})
                    self.assertEqual(window.combo_post.currentIndex(), 0)
                    self.assertEqual(window.label_midia.text(), "First")
                    window.combo_post.setCurrentIndex(2)
                    self.assertEqual(window.combo_post.currentData(), 3)
                    self.assertEqual(window.label_midia.text(), "Second")
                    opts = app.criar_opcoes_download("mp4", ROOT / "work", None, False,
                                                    post_metadata=window._post_metadata, selected_video=3)
                    self.assertEqual(opts["playlist_items"], "3")
                    self.assertIn("%(id)s", opts["outtmpl"])
                    window.input_url.setText("https://x.com/name/status/12345")
                    window._preview_timer.stop()
                    window._buscar_previa()
                    old = Lookup.instances[-1]
                    window.input_url.clear()
                    self.assertTrue(old.cancelled)
                    old.finished.emit({"url": old.url, "videos": [{"index": 1, "title": "Stale"}]})
                    self.assertIsNone(window._post_metadata)
                    self.assertEqual(window.label_midia.text(), "A mídia aparecerá aqui")
                    self.assertEqual(window.progress_bar.value(), 0)
                finally: window.close(); window.deleteLater(); QTest.qWait(10)

    def test_preview_error_is_silent_explicit_error_is_visible(self):
        spec = importlib.util.spec_from_file_location("source_error_ui", ROOT / "baixarMusicaYouTube/baixar_musica_qt.py")
        app = importlib.util.module_from_spec(spec); spec.loader.exec_module(app)
        class Lookup(QObject):
            finished = Signal(dict)
            failed = Signal(str)
            def __init__(self, _entry, _url, _timeout, parent): super().__init__(parent)
            def start(self): QTimer.singleShot(0, lambda: self.failed.emit("fixture unavailable"))
            def cancel(self): pass
        with patch.object(app, "MetadataLookup", Lookup):
            window = app.JanelaPrincipal(self.settings)
            try:
                window.input_url.setText("https://instagram.com/p/ABC/")
                window._preview_timer.stop(); window._buscar_previa(); QTest.qWait(10)
                self.assertTrue(window.label_erro.isHidden())
                self.assertTrue(window.btn_baixar.isEnabled())
                window._consultar_post(window._preview_target, explicit=True); QTest.qWait(10)
                self.assertFalse(window.label_erro.isHidden())
                self.assertFalse(window._working)
            finally: window.close(); window.deleteLater(); QTest.qWait(10)

    def test_explicit_multi_video_discovery_waits_for_another_click(self):
        spec = importlib.util.spec_from_file_location("source_explicit_ui", ROOT / "baixarMusicaYouTube/baixar_musica_qt.py")
        app = importlib.util.module_from_spec(spec); spec.loader.exec_module(app)
        class Lookup(QObject):
            finished = Signal(dict)
            failed = Signal(str)
            def __init__(self, _entry, url, _timeout, parent): super().__init__(parent); self.url = url
            def start(self):
                QTimer.singleShot(0, lambda: self.finished.emit({"url": self.url, "source": "instagram", "videos": [
                    {"index": 1, "title": "First"}, {"index": 2, "title": "Second"}]}))
            def cancel(self): pass
        with patch.object(app, "MetadataLookup", Lookup):
            window = app.JanelaPrincipal(self.settings)
            try:
                window.input_url.setText("https://instagram.com/p/ABC/")
                window._preview_timer.stop()
                with patch.object(window, "_iniciar_download") as start:
                    window._consultar_post(window._preview_target, explicit=True); QTest.qWait(10)
                    start.assert_not_called()
                self.assertFalse(window._working)
                self.assertIsNone(window.worker_thread)
                self.assertFalse(window._post_box.isHidden())
                self.assertIsNone(window.combo_post.currentData())
                self.assertIn("clique em Baixar", window.label_status.text())
            finally: window.close(); window.deleteLater(); QTest.qWait(10)


class WorkerPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.apps = []
        for folder in ("baixarMusicaYouTube", "baixarMusicaYouTubeLinux"):
            spec = importlib.util.spec_from_file_location("source_worker_" + folder, ROOT / folder / "baixar_musica_qt.py")
            app = importlib.util.module_from_spec(spec); spec.loader.exec_module(app)
            cls.apps.append(app)

    def test_other_site_403_never_uses_youtube_fallbacks(self):
        from unittest.mock import MagicMock
        for app in self.apps:
            with self.subTest(app=app.__name__):
                backend = MagicMock()
                backend.return_value.__enter__.return_value.download.side_effect = RuntimeError("HTTP Error 403")
                worker = app.DownloadWorker("https://instagram.com/p/ABC/", ROOT / "work", "mp4", False)
                errors, completed = [], []
                worker.download_erro.connect(errors.append)
                worker.download_concluido.connect(lambda: completed.append(True))
                with patch.object(app, "verificar_dependencias"), patch.object(app, "YoutubeDL", backend):
                    worker.run()
                self.assertEqual(backend.call_count, 1)
                self.assertIn("Instagram", errors[0])
                self.assertFalse(completed)

    def test_partial_download_reports_saved_files_without_success(self):
        for app in self.apps:
            with self.subTest(app=app.__name__), tempfile.TemporaryDirectory() as directory:
                saved = Path(directory) / "second-2-Same title.mp4"
                saved.write_bytes(b"completed fixture")
                class Backend:
                    def __init__(self, options): self.options = options
                    def __enter__(self): return self
                    def __exit__(self, *_): pass
                    def download(self, _urls):
                        for hook in self.options["postprocessor_hooks"]:
                            hook({"status": "finished", "info_dict": {"filepath": str(saved)}})
                        return 1
                metadata = {"url": "https://instagram.com/p/ABC/", "videos": [{"index": 1}, {"index": 2}]}
                worker = app.DownloadWorker(metadata["url"], directory, "mp4", False, post_metadata=metadata)
                errors, completed = [], []
                worker.download_erro.connect(errors.append)
                worker.download_concluido.connect(lambda: completed.append(True))
                with patch.object(app, "verificar_dependencias"), patch.object(app, "YoutubeDL", Backend):
                    worker.run()
                self.assertIn("Download parcial: 1 arquivo(s)", errors[0])
                self.assertTrue(saved.is_file())
                self.assertFalse(completed)
