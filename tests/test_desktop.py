import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
APPS = []
for folder in ("baixarMusicaYouTube", "baixarMusicaYouTubeLinux"):
    spec = importlib.util.spec_from_file_location(folder, ROOT / folder / "baixar_musica_qt.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    APPS.append(module)


class DesktopRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def test_youtube_domains_and_playlist_choice(self):
        for app in APPS:
            self.assertTrue(app.url_do_youtube("https://youtu.be/example"))
            self.assertTrue(app.url_do_youtube("https://www.youtube.com/watch?v=example"))
            self.assertFalse(app.url_do_youtube("https://youtube.com.example.org/watch?v=x"))
            self.assertFalse(app.url_do_youtube("https://vimeo.com/1"))
            url = "https://www.youtube.com/watch?v=x&list=abc&t=2"
            self.assertTrue(app.url_tem_playlist(url))
            single = app.remover_playlist_da_url(url)
            self.assertFalse(app.url_tem_playlist(single))
            self.assertIn("v=x", single)
            self.assertIn("t=2", single)

    def test_gif_valid_times_and_boundaries(self):
        for app in APPS:
            self.assertEqual(app.validar_intervalo_gif("00:05", "00:08"), (5, 8))
            self.assertEqual(app.validar_intervalo_gif("1:00:00", "1:00:30"), (3600, 3630))
            self.assertEqual(app.converter_tempo_para_segundos("2,5", "inicial"), 2.5)
            for start, end in [("", "2"), ("nan", "2"), ("-1", "2"), ("2", "2"), ("3", "2"), ("0", "31"), ("1:60", "122")]:
                with self.subTest(app=app.__name__, start=start, end=end), self.assertRaises(ValueError):
                    app.validar_intervalo_gif(start, end)

    def test_no_implicit_or_bundled_cookies(self):
        for app in APPS:
            with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"UIFOR_YTDLP_COOKIES": ""}):
                legacy = Path(tmp) / "www.youtube.com_cookies.txt"
                legacy.write_text("# synthetic fixture", encoding="utf-8")
                with patch.object(app, "caminho_recurso", side_effect=lambda name: Path(tmp) / name):
                    self.assertIsNone(app.caminho_cookies())
                    self.assertNotIn("cookiefile", app.opcoes_base())
                with patch.dict(os.environ, {"UIFOR_YTDLP_COOKIES": str(legacy)}):
                    self.assertEqual(app.opcoes_base()["cookiefile"], str(legacy))
                with patch.dict(os.environ, {"UIFOR_YTDLP_COOKIES": str(Path(tmp) / "missing.txt")}):
                    with self.assertRaisesRegex(RuntimeError, "UIFOR_YTDLP_COOKIES"):
                        app.opcoes_base()

    def test_tool_precedence_and_missing_dependency_message(self):
        for app in APPS:
            with tempfile.TemporaryDirectory() as tmp:
                suffix = ".exe" if os.name == "nt" else ""
                local = Path(tmp) / "bin" / ("ffmpeg" + suffix)
                local.parent.mkdir()
                local.touch()
                with patch.object(app, "caminho_recurso", side_effect=lambda name: Path(tmp) / name), patch.object(app.shutil, "which", return_value=None):
                    self.assertEqual(app.caminho_ffmpeg(), local)
                with patch.object(app, "caminho_ferramenta", return_value=None):
                    with self.assertRaisesRegex(RuntimeError, "ffmpeg, ffprobe, deno"):
                        app.verificar_dependencias()

    def test_formats_and_worker_error_reset(self):
        for app in APPS:
            with patch.dict(os.environ, {"UIFOR_YTDLP_COOKIES": ""}):
                self.assertEqual(set(app.FORMATOS_SAIDA.values()), {"mp4", "mp3", "webm", "mkv", "gif", "wav"})
                for kind in app.FORMATOS_SAIDA.values():
                    options = app.criar_opcoes_download(kind, "output", None, False, 1, 3)
                    self.assertTrue(options["noplaylist"])
                    self.assertNotIn("cookiefile", options)
                window = app.JanelaPrincipal()
                self.assertEqual((window.width(), window.height()), (980, 760))
                self.assertEqual(window.minimumSize(), window.maximumSize())
                window.btn_baixar.setEnabled(False)
                worker = app.DownloadWorker("https://youtu.be/example", ".", "mp4", False)
                errors = []
                worker.download_erro.connect(errors.append)
                worker.download_erro.connect(window._download_erro)
                with patch.object(app, "verificar_dependencias", side_effect=RuntimeError("fixture failure")), patch.object(app.QMessageBox, "critical"):
                    worker.run()
                self.assertEqual(errors, ["fixture failure"])
                self.assertTrue(window.btn_baixar.isEnabled())
                self.assertTrue(window.combo_formato.isEnabled())
                self.assertEqual((window.progress_bar.minimum(), window.progress_bar.maximum()), (0, 100))
                for index, kind in enumerate(app.FORMATOS_SAIDA.values()):
                    window.combo_formato.setCurrentIndex(index)
                    window._atualizar_opcoes_formato()
                    self.assertEqual(not window._opcoes_gif.isHidden(), kind == "gif")
                window.close()


if __name__ == "__main__":
    unittest.main()
