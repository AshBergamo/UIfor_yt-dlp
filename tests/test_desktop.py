import importlib.util
import json
import os
from pathlib import Path
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings, Qt, QBuffer, QByteArray, QIODevice, QUrl
from PySide6.QtGui import QImage, QColor, QPixmap, QPalette
from PySide6.QtTest import QTest

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

    def test_preview_video_links(self):
        video_id = 'jNQXAC9IVRw'
        expected = f'https://www.youtube.com/watch?v={video_id}'
        for app in APPS:
            self.assertEqual(app.normalizar_url(url=f' youtu.be/{video_id} '), f'https://youtu.be/{video_id}')
            for link in [expected + '&list=example&t=2', f'youtu.be/{video_id}?si=test',
                         f'https://m.youtube.com/shorts/{video_id}', f'https://youtube.com/live/{video_id}',
                         f'https://www.youtube.com/embed/{video_id}']:
                self.assertEqual(app.url_video_previa(link), expected)
            for link in ['', 'https://[', 'https://youtube.com/watch?v=partial',
                         'https://youtube.com/playlist?list=test',
                         f'https://youtube.com.example.org/watch?v={video_id}',
                         f'file://youtube.com/watch?v={video_id}']:
                self.assertEqual(app.url_video_previa(link), '')

    def test_preview_debounce_silent_errors_and_stale_results(self):
        image = QImage(24, 16, QImage.Format.Format_RGB32)
        image.fill(QColor('blue'))
        data = QByteArray()
        buffer = QBuffer(data)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, 'PNG')
        buffer.close()
        payload = bytes(data)
        requests, gates, started = [], {}, {}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/image':
                    body, status = payload, 200
                else:
                    identity = self.path.rsplit('/', 1)[-1]
                    requests.append(identity)
                    if identity in gates:
                        started[identity].set()
                        gates[identity].wait(3)
                    info = {'title': 'Vídeo ' + identity,
                            'thumbnail_url': f'http://127.0.0.1:{self.server.server_port}/image'}
                    body, status = json.dumps(info).encode(), 200
                    if identity == 'FFFFFFFFFFF':
                        body, status = b'Not found', 404
                    elif identity == 'CCCCCCCCCCC':
                        body = b'not JSON'
                    elif identity == 'DDDDDDDDDDD':
                        body = b'x' * (128 * 1024 + 1)
                self.send_response(status)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                try:
                    self.wfile.write(body)
                except OSError:
                    pass  # The UI may cancel an obsolete request.

            def log_message(self, *_):
                pass

        def wait_for(condition):
            deadline = time.monotonic() + 3
            while not condition() and time.monotonic() < deadline:
                QTest.qWait(10)
            self.assertTrue(condition())

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            for app in APPS:
                with tempfile.TemporaryDirectory() as tmp:
                    window = app.JanelaPrincipal(QSettings(str(Path(tmp) / 'ui.ini'), QSettings.Format.IniFormat))
                    window._preview_timer.setInterval(40)
                    window._url_consulta_previa = lambda target: QUrl(f'http://127.0.0.1:{server.server_port}/' + target.rsplit('=', 1)[-1])
                    requests.clear()
                    window.input_url.setText('https://youtu.be/AAAAAAAAAAA')
                    QTest.qWait(10)
                    window.input_url.setText('https://youtu.be/BBBBBBBBBBB')
                    wait_for(lambda: not window.thumbnail.pixmap.isNull())
                    self.assertEqual(requests, ['BBBBBBBBBBB'])
                    self.assertEqual(window.label_midia.text(), 'Vídeo BBBBBBBBBBB')
                    self.assertEqual(window.thumbnail.pixmap.toImage().pixelColor(0, 0), QColor('blue'))
                    self.assertTrue(window.fundo.tem_imagem())
                    self.assertIsNone(window.worker_thread)
                    self.assertEqual(window.progress_bar.value(), 0)
                    self.assertTrue(window.btn_baixar.isEnabled())
                    window._aplicar_tema('claro')
                    self.assertEqual(window.label_midia.text(), 'Vídeo BBBBBBBBBBB')

                    gates['AAAAAAAAAAA'], started['AAAAAAAAAAA'] = threading.Event(), threading.Event()
                    window.input_url.setText('https://youtu.be/AAAAAAAAAAA')
                    self.assertFalse(window.fundo.tem_imagem())
                    wait_for(started['AAAAAAAAAAA'].is_set)
                    window.input_url.setText('https://youtu.be/BBBBBBBBBBB')
                    wait_for(lambda: window._preview_loaded)
                    gates['AAAAAAAAAAA'].set()
                    QTest.qWait(100)
                    self.assertEqual(window.label_midia.text(), 'Vídeo BBBBBBBBBBB')
                    wait_for(lambda: not window.thumbnail.pixmap.isNull())
                    self.assertTrue(window.fundo.tem_imagem())

                    for identity in ['FFFFFFFFFFF', 'CCCCCCCCCCC', 'DDDDDDDDDDD']:
                        window.input_url.setText('https://youtu.be/' + identity)
                        wait_for(lambda: identity in requests and window._preview_reply is None)
                        self.assertFalse(window._preview_loaded)
                        self.assertEqual(window.label_midia.text(), 'A mídia aparecerá aqui')
                        self.assertTrue(window.thumbnail.pixmap.isNull())
                        self.assertFalse(window.fundo.tem_imagem())
                        self.assertTrue(window.label_erro.isHidden())
                        self.assertTrue(window.btn_baixar.isEnabled())
                        self.assertFalse(window._working)

                    gates['AAAAAAAAAAA'], started['AAAAAAAAAAA'] = threading.Event(), threading.Event()
                    window.input_url.setText('https://youtu.be/AAAAAAAAAAA')
                    wait_for(started['AAAAAAAAAAA'].is_set)
                    window._set_working(True)
                    window._atualizar_metadata({'title': 'From download', 'thumbnail': ''})
                    window._atualizar_progresso('Baixando', 42, 100)
                    gates['AAAAAAAAAAA'].set()
                    QTest.qWait(100)
                    self.assertEqual(window.label_midia.text(), 'From download')
                    self.assertEqual(window.progress_bar.value(), 42)
                    self.assertFalse(window.btn_baixar.isEnabled())
                    window._set_working(False)
                    window.input_url.clear()
                    self.assertEqual(window.label_midia.text(), 'A mídia aparecerá aqui')
                    self.assertIsNone(window._preview_reply)
                    self.assertFalse(window.fundo.tem_imagem())
                    window.close()
        finally:
            for gate in gates.values():
                gate.set()
            server.shutdown()
            server.server_close()
            thread.join()

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
            with patch.dict(os.environ, {"UIFOR_YTDLP_COOKIES": ""}), tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(set(app.FORMATOS_SAIDA.values()), {"mp4", "mp3", "webm", "mkv", "gif", "wav"})
                for kind in app.FORMATOS_SAIDA.values():
                    options = app.criar_opcoes_download(kind, "output", None, False, 1, 3)
                    self.assertTrue(options["noplaylist"])
                    self.assertNotIn("cookiefile", options)
                settings = QSettings(str(Path(tmp) / 'ui.ini'), QSettings.Format.IniFormat)
                window = app.JanelaPrincipal(settings)
                self.assertLess(window.minimumWidth(), window.maximumWidth())
                self.assertLess(window.minimumHeight(), window.maximumHeight())
                window.btn_baixar.setEnabled(False)
                worker = app.DownloadWorker("https://youtu.be/example", ".", "mp4", False)
                errors = []
                worker.download_erro.connect(errors.append)
                worker.download_erro.connect(window._download_erro)
                with patch.object(app, "verificar_dependencias", side_effect=RuntimeError("fixture failure")), patch.object(app.QMessageBox, "critical"):
                    worker.run()
                self.assertEqual(len(errors), 1)
                self.assertIn("fixture failure", errors[0])
                self.assertIn("Não foi possível", errors[0])
                self.assertTrue(window.btn_baixar.isEnabled())
                self.assertTrue(window.combo_formato.isEnabled())
                self.assertEqual((window.progress_bar.minimum(), window.progress_bar.maximum()), (0, 100))
                for index, kind in enumerate(app.FORMATOS_SAIDA.values()):
                    window.combo_formato.setCurrentIndex(index)
                    window._atualizar_opcoes_formato()
                    self.assertEqual(not window._opcoes_gif.isHidden(), kind == "gif")
                window.close()

    def test_remux_options_preserve_routes_covers_and_independent_state(self):
        cases = [
            ("mp4", "bestvideo*+bestaudio/best", "mp4", None),
            ("mp4_android_vr", "bestvideo*+bestaudio/best", "mp4", {"youtube": {"player_client": ["android_vr"]}}),
            ("mp4_compat", "best[ext=mp4]/best", "mp4", None),
            ("mkv", "bestvideo*+bestaudio/best", "mkv", None),
        ]
        metadata = {"videos": [{"index": 2}, {"index": 4}]}
        for app in APPS:
            with patch.dict(os.environ, {"UIFOR_YTDLP_COOKIES": ""}):
                options_by_route = {}
                for kind, selector, container, extractor_args in cases:
                    with self.subTest(app=app.__name__, route=kind):
                        options = app.criar_opcoes_download(kind, "output", None, False)
                        options_by_route[kind] = options
                        self.assertEqual(options["format"], selector)
                        self.assertEqual(options["merge_output_format"], container)
                        self.assertEqual(options["outtmpl"], str(Path("output") / "%(title)s.%(ext)s"))
                        self.assertEqual(options["postprocessors"], [
                            {"key": "FFmpegVideoRemuxer", "preferedformat": container},
                            {"key": "FFmpegThumbnailsConvertor", "format": "jpg", "when": "before_dl"},
                            {"key": "EmbedThumbnail", "already_have_thumbnail": False},
                        ])
                        self.assertTrue(options["writethumbnail"])
                        if extractor_args is None:
                            self.assertNotIn("extractor_args", options)
                        else:
                            self.assertEqual(options["extractor_args"], extractor_args)

                        selected = app.criar_opcoes_download(kind, "output", None, True,
                                                            post_metadata=metadata, selected_video=4)
                        self.assertEqual(selected["playlist_items"], "4")
                        self.assertTrue(selected["noplaylist"])
                        self.assertFalse(selected["ignoreerrors"])
                        self.assertEqual(selected["outtmpl"], str(Path("output") / "%(id)s-%(playlist_index|1)s-%(title).150B.%(ext)s"))

                # Mutating one download must not affect another route or call.
                options_by_route["mp4"]["postprocessors"][0]["preferedformat"] = "fixture"
                options_by_route["mp4"]["postprocessors"][1]["format"] = "fixture"
                options_by_route["mp4"]["postprocessors"][2]["already_have_thumbnail"] = True
                options_by_route["mp4_android_vr"]["extractor_args"]["youtube"]["player_client"].append("fixture")
                for kind, _, container, extractor_args in cases:
                    with self.subTest(app=app.__name__, fresh_route=kind):
                        fresh = app.criar_opcoes_download(kind, "output", None, False)
                        self.assertEqual(fresh["postprocessors"][0]["preferedformat"], container)
                        self.assertEqual(fresh["postprocessors"][1]["format"], "jpg")
                        self.assertFalse(fresh["postprocessors"][2]["already_have_thumbnail"])
                        if extractor_args is None:
                            self.assertNotIn("extractor_args", fresh)
                        else:
                            self.assertEqual(fresh["extractor_args"], extractor_args)
                        if kind != "mp4":
                            self.assertEqual(options_by_route[kind]["postprocessors"][0]["preferedformat"], container)

    def test_theme_preserves_form_and_active_progress_and_persists(self):
        for app in APPS:
            with tempfile.TemporaryDirectory() as tmp:
                settings = QSettings(str(Path(tmp) / 'ui.ini'), QSettings.Format.IniFormat)
                window = app.JanelaPrincipal(settings)
                window.input_url.setText('https://youtu.be/example')
                window.combo_formato.setCurrentIndex(4)
                window.input_gif_inicio.setText('00:01')
                window.input_gif_fim.setText('00:03')
                window.check_playlist.setChecked(True)
                window._set_working(True)
                window._atualizar_progresso('Baixando', 42, 100)
                window._aplicar_tema('claro')
                self.assertEqual(window.input_url.text(), 'https://youtu.be/example')
                self.assertEqual(window._formato_selecionado(), 'gif')
                self.assertEqual(window.input_gif_inicio.text(), '00:01')
                self.assertTrue(window.check_playlist.isChecked())
                self.assertEqual(window.progress_bar.value(), 42)
                self.assertFalse(window.btn_baixar.isEnabled())
                self.assertTrue(window.btn_sobre.isEnabled())
                window._download_erro('fixture')
                self.assertFalse(window.label_erro.isHidden())
                self.assertEqual(window.label_percentual.text(), '0%')
                window.close()
                restored = app.JanelaPrincipal(settings)
                self.assertEqual(restored.tema, 'claro')
                restored.close()

    def test_original_thumbnail_optional_and_bounded(self):
        source = QImage(24, 16, QImage.Format.Format_RGB32)
        source.fill(QColor('red'))
        data = QByteArray()
        buffer = QBuffer(data)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        source.save(buffer, 'PNG')
        buffer.close()
        payload = bytes(data)

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200 if self.path == '/original' else 404)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *_):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            for app in APPS:
                with tempfile.TemporaryDirectory() as tmp:
                    window = app.JanelaPrincipal(QSettings(str(Path(tmp) / 'ui.ini'), QSettings.Format.IniFormat))
                    window._set_working(True)
                    window._atualizar_progresso('Baixando', 42, 100)

                    def fetch(path):
                        window._atualizar_metadata({'title': 'Original fixture', 'thumbnail': f'http://127.0.0.1:{server.server_port}/{path}'})
                        deadline = time.monotonic() + 5
                        while window._thumbnail_reply is not None and time.monotonic() < deadline:
                            QTest.qWait(10)
                        self.assertIsNone(window._thumbnail_reply)

                    fetch('original')
                    self.assertFalse(window.thumbnail.pixmap.isNull())
                    self.assertTrue(window.fundo.tem_imagem())
                    self.assertEqual(window.thumbnail.pixmap.toImage().pixelColor(0, 0), QColor('red'))
                    window._aplicar_tema('claro')
                    self.assertFalse(window.thumbnail.pixmap.isNull())
                    fetch('missing')
                    self.assertTrue(window.thumbnail.pixmap.isNull())
                    self.assertFalse(window.fundo.tem_imagem())
                    self.assertTrue(window._working)
                    self.assertEqual(window.progress_bar.value(), 42)
                    self.assertTrue(window.label_erro.isHidden())
                    window.MAX_THUMBNAIL_BYTES = 32
                    fetch('original')
                    self.assertTrue(window.thumbnail.pixmap.isNull())
                    self.assertTrue(window._working)
                    window._atualizar_metadata({'title': 'No image', 'thumbnail': 'file:///unavailable'})
                    self.assertIsNone(window._thumbnail_reply)
                    window.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_background_cache_is_bounded_soft_and_keeps_original(self):
        original = QImage(1600, 900, QImage.Format.Format_RGB32)
        original.fill(QColor('red'))
        for y in range(300, 600):
            for x in range(600, 1000):
                original.setPixelColor(x, y, QColor('blue'))
        for app in APPS:
            prepared = app.FundoMidia.preparar_imagem(original).toImage()
            self.assertEqual((prepared.width(), prepared.height()), (640, 360))
            self.assertEqual(original.pixelColor(600, 450), QColor('blue'))
            # A sharp edge is softened; solid regions and their opacity survive.
            edge = prepared.pixelColor(240, 180)
            self.assertGreater(edge.red(), 0)
            self.assertGreater(edge.blue(), 0)
            self.assertLess(edge.red(), 255)
            self.assertEqual(prepared.pixelColor(0, 0).alpha(), 255)
            self.assertEqual(prepared.pixelColor(639, 359).alpha(), 255)
            self.assertGreater(prepared.pixelColor(320, 180).blue(), 250)

    def test_background_lifecycle_cache_and_optional_failure(self):
        original = QImage(90, 160, QImage.Format.Format_RGB32)
        original.fill(QColor('#e84d23'))
        for app in APPS:
            with tempfile.TemporaryDirectory() as tmp:
                window = app.JanelaPrincipal(QSettings(str(Path(tmp) / 'ui.ini'), QSettings.Format.IniFormat))
                window.show()
                QTest.qWait(10)
                changes = []
                window.fundo.imagem_alterada.connect(changes.append)
                with patch.object(app.FundoMidia, 'preparar_imagem', wraps=app.FundoMidia.preparar_imagem) as prepare:
                    field_before = window.input_url.grab().toImage()
                    window.thumbnail.pixmap = QPixmap.fromImage(original)
                    window.fundo.definir_imagem(original)
                    QTest.qWait(300)
                    self.assertEqual(changes, [True])
                    self.assertTrue(window._form.property('wallpaper'))
                    self.assertEqual(window.input_url.grab().toImage(), field_before)
                    cached = window.fundo._imagem.cacheKey()
                    window._aplicar_tema('claro')
                    window.resize(780, 600)
                    self.qt.processEvents()
                    window.scroll_area.verticalScrollBar().setValue(100)
                    window.fundo.grab()
                    self.assertEqual(prepare.call_count, 1)
                    self.assertEqual(window.fundo._imagem.cacheKey(), cached)
                    self.assertEqual(window.thumbnail.pixmap.toImage(), original)
                    # Starting work and reporting the same thumbnail keep artwork.
                    window._thumbnail_url = 'https://example.com/original.jpg'
                    window._set_working(True)
                    window._atualizar_metadata({'title': 'Current video', 'thumbnail': window._thumbnail_url})
                    self.assertTrue(window.fundo.tem_imagem())
                    self.assertEqual(prepare.call_count, 1)
                    window._set_working(False)
                    window._limpar_thumbnail()
                    self.assertFalse(window._form.property('wallpaper'))
                    self.assertEqual(changes, [True, False])
                with patch.object(app.FundoMidia, 'preparar_imagem', side_effect=MemoryError):
                    window.fundo.definir_imagem(original)
                    self.assertFalse(window.fundo.tem_imagem())
                    self.assertTrue(window.label_erro.isHidden())
                    self.assertTrue(window.btn_baixar.isEnabled())
                window.fundo.definir_imagem(original)
                window.close()
                self.assertFalse(window.fundo.tem_imagem())

    def test_background_center_crop_covers_wide_and_portrait_views(self):
        source = QImage(400, 100, QImage.Format.Format_RGB32)
        source.fill(QColor('red'))
        for y in range(100):
            for x in range(150, 250):
                source.setPixelColor(x, y, QColor('blue'))
        for app in APPS:
            background = app.FundoMidia()
            background.definir_imagem(source)
            background._animacao.stop()
            background.intensidade = 1
            for width, height in [(200, 400), (800, 200)]:
                background.resize(width, height)
                rendered = background.grab().toImage()
                center = rendered.pixelColor(width // 2, height // 2)
                self.assertGreater(center.blue(), center.red() + 60)
                corner = rendered.pixelColor(1, 1)
                self.assertEqual(corner.alpha(), 255)
                if height > width:  # Both red edges are cropped, never stretched inwards.
                    self.assertGreater(corner.blue(), corner.red() + 60)
                else:
                    self.assertGreater(corner.red(), corner.blue() + 50)
            background.limpar()
            background.close()

    def test_background_text_contrast_for_extreme_images(self):
        def luminance(color):
            values = [channel / 255 for channel in (color.red(), color.green(), color.blue())]
            values = [value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4 for value in values]
            return sum(weight * value for weight, value in zip((.2126, .7152, .0722), values))

        def contrast(a, b):
            low, high = sorted((luminance(a), luminance(b)))
            return (high + .05) / (low + .05)

        for app in APPS:
            with tempfile.TemporaryDirectory() as tmp:
                window = app.JanelaPrincipal(QSettings(str(Path(tmp) / 'ui.ini'), QSettings.Format.IniFormat))
                for theme in ('escuro', 'claro'):
                    window._aplicar_tema(theme)
                    for color in ('black', 'white'):
                        image = QImage(24, 16, QImage.Format.Format_RGB32)
                        image.fill(QColor(color))
                        window.fundo.definir_imagem(image)
                        window.fundo._animacao.stop()
                        window.fundo.intensidade = 1
                        background = app.FundoMidia()
                        background.definir_tema(theme)
                        background.definir_imagem(image)
                        background._animacao.stop()
                        background.intensidade = 1
                        background.resize(200, 200)
                        rendered = background.grab().toImage()
                        caption = window._legendas_fundo[0].palette().color(QPalette.ColorRole.WindowText)
                        for x in range(0, rendered.width(), max(1, rendered.width() // 8)):
                            for y in range(0, rendered.height(), max(1, rendered.height() // 8)):
                                base = rendered.pixelColor(x, y)
                                self.assertGreaterEqual(contrast(caption, base), 4.5)
                                panel = QColor(app.THEMES[theme]['panel'])
                                blended = QColor(*[round(f * 214 / 255 + b * 41 / 255) for f, b in zip(
                                    (panel.red(), panel.green(), panel.blue()), (base.red(), base.green(), base.blue()))])
                                for role in ('text', 'muted', 'error'):
                                    self.assertGreaterEqual(contrast(QColor(app.THEMES[theme][role]), blended), 4.5)
                        background.close()
                window.close()

    def test_worker_reports_media_and_indeterminate_conversion(self):
        for app in APPS:
            metadata, progress, completed = [], [], []
            worker = app.DownloadWorker('https://youtu.be/example', '.', 'mp4', False)
            worker.metadata_atualizada.connect(metadata.append)
            worker.progresso_atualizado.connect(lambda *args: progress.append(args))
            worker.download_concluido.connect(lambda: completed.append(True))

            class Downloader:
                def __init__(self, options):
                    self.options = options

                def __enter__(self):
                    return self

                def __exit__(self, *_):
                    pass

                def download(self, urls):
                    for identity in ['first', 'first', 'second']:
                        self.options['progress_hooks'][0]({'status': 'downloading', 'downloaded_bytes': 123,
                            'info_dict': {'id': identity, 'title': identity, 'playlist_index': 1 if identity == 'first' else 2,
                                          'thumbnail': 'https://example.com/original.jpg'}})
                    self.options['postprocessor_hooks'][0]({'status': 'started'})

            with patch.object(app, 'verificar_dependencias'), patch.object(app, 'YoutubeDL', Downloader), patch.dict(os.environ, {'UIFOR_YTDLP_COOKIES': ''}):
                worker.run()
            self.assertEqual([item['title'] for item in metadata], ['first', 'second'])
            self.assertEqual(metadata[0]['thumbnail'], 'https://example.com/original.jpg')
            self.assertTrue(any(maximum == 0 for _, _, maximum in progress))
            self.assertEqual(completed, [True])
            worker.playlist = True
            progress.clear()
            with patch.object(app, 'verificar_dependencias'), patch.object(app, 'YoutubeDL', Downloader), patch.object(app, 'contar_videos_playlist', return_value=2), patch.dict(os.environ, {'UIFOR_YTDLP_COOKIES': ''}):
                worker.run()
            self.assertTrue(any('Vídeo 1 de 2' in text for text, _, _ in progress))
            self.assertTrue(any('Vídeo 2 de 2' in text for text, _, _ in progress))

    def test_native_maximized_window_and_restore(self):
        for app in APPS:
            with tempfile.TemporaryDirectory() as tmp:
                settings = QSettings(str(Path(tmp) / 'ui.ini'), QSettings.Format.IniFormat)
                window = app.JanelaPrincipal(settings)
                window.mostrar()
                self.qt.processEvents()
                self.assertTrue(window.isMaximized())
                self.assertFalse(window.isFullScreen())
                self.assertTrue(window.windowFlags() & Qt.WindowType.WindowMaximizeButtonHint)
                window.showNormal()
                window.resize(800, 600)
                self.qt.processEvents()
                window.close()
                restored = app.JanelaPrincipal(settings)
                restored.mostrar()
                self.qt.processEvents()
                self.assertFalse(restored.isMaximized())
                self.assertFalse(restored.isFullScreen())
                self.assertLessEqual(abs(restored.width() - 800), 4)  # Offscreen screen includes a small native frame.
                restored.close()


if __name__ == "__main__":
    unittest.main()
