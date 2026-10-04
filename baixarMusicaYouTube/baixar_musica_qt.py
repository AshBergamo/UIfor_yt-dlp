import math
import json
import os
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from PySide6.QtCore import (Qt, QThread, Signal, QObject, QSettings, QUrl, QRectF,
                           QPointF, QTimer, Property, QPropertyAnimation, QEasingCurve)
from PySide6.QtGui import (QIcon, QFontDatabase, QColor, QPainter, QPen, QPixmap, QImage,
                           QPolygonF, QPainterPath, QPalette, QDesktopServices, QLinearGradient)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QLineEdit, QPushButton, QProgressBar, QFileDialog,
                              QMessageBox, QFrame, QSizePolicy, QScrollArea, QBoxLayout,
                              QGridLayout, QButtonGroup, QCheckBox, QStyle, QStyleOptionButton,
                              QGraphicsScene, QGraphicsBlurEffect, QComboBox)

try:
    from yt_dlp import YoutubeDL
    from yt_dlp.utils import download_range_func
except ImportError:
    YoutubeDL = None
    download_range_func = None

if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from media_sources import (classify_url, resolve_url, SOURCE_HELP, EXTRACTORS,
                           selection_options, media_filter, friendly_error,
                           normalize_url)
from metadata_ipc import MetadataLookup, run_helper

ARQUIVO_ICONE = "pixil-frame-0.png"
DOMINIOS_YOUTUBE = ("youtube.com", "youtu.be")

FORMATOS_SAIDA = {
    "MP4 (Vídeo)": "mp4",
    "MP3 (Áudio)": "mp3",
    "WEBM (Vídeo) - Formato Web": "webm",
    "MKV (Vídeo)": "mkv",
    "GIF (Animação)": "gif",
    "WAV (Áudio)": "wav",
}

FORMATO_MELHOR_QUALIDADE = "bestvideo*+bestaudio/best"
POS_PROCESSADOR_MP4 = {
    "key": "FFmpegVideoRemuxer",
    "preferedformat": "mp4",
}
POS_PROCESSADOR_MKV = {
    "key": "FFmpegVideoRemuxer",
    "preferedformat": "mkv",
}
FILTRO_GIF = (
    "fps=15,scale=w='min(720,iw)':h=-2:flags=lanczos,"
    "split[quadros][paleta];"
    "[paleta]palettegen=max_colors=256:stats_mode=diff[cores];"
    "[quadros][cores]paletteuse=dither=sierra2_4a:diff_mode=rectangle"
)
DURACAO_MAXIMA_GIF = 30

def caminho_recurso(nome_arquivo):
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent
    return base / nome_arquivo


def caminho_ferramenta(nome):
    arquivo = f"{nome}.exe" if sys.platform.startswith("win") else nome
    for candidato in (caminho_recurso("bin") / arquivo, caminho_recurso(arquivo)):
        if candidato.is_file():
            return candidato
    encontrado = shutil.which(nome)
    return Path(encontrado) if encontrado else None


def caminho_ffmpeg():
    return caminho_ferramenta("ffmpeg")


def caminho_cookies():
    configurado = os.environ.get("UIFOR_YTDLP_COOKIES", "").strip()
    if not configurado:
        return None
    arquivo = Path(configurado).expanduser()
    if not arquivo.is_file():
        raise RuntimeError("UIFOR_YTDLP_COOKIES deve indicar um arquivo de cookies existente.")
    return arquivo


def verificar_dependencias():
    if YoutubeDL is None:
        raise RuntimeError("Instale as dependências do aplicativo com requirements.txt.")
    faltando = [nome for nome in ("ffmpeg", "ffprobe", "deno") if caminho_ferramenta(nome) is None]
    if faltando:
        raise RuntimeError("Ferramentas não encontradas: " + ", ".join(faltando) + ". Consulte o README.")
    try:
        import yt_dlp_ejs
    except ImportError:
        raise RuntimeError("Instale yt-dlp com os extras default para incluir os componentes EJS.") from None


def caminho_icone():
    return caminho_recurso(ARQUIVO_ICONE)


def normalizar_url(url):
    return normalize_url(url)


def url_do_youtube(url):
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return host in DOMINIOS_YOUTUBE or host.endswith(".youtube.com")


def url_tem_playlist(url):
    if not url_do_youtube(url):
        return False
    parametros = dict(parse_qsl(urlparse(url).query, keep_blank_values=True))
    return bool(parametros.get("list"))


def url_video_previa(url):
    """Normalize video links for a small, public oEmbed request, without downloading."""
    try:
        parsed = urlparse(normalizar_url(url))
        if parsed.scheme not in {"http", "https"} or not url_do_youtube(parsed.geturl()):
            return ""
        parts = parsed.path.strip("/").split("/")
        video_id = ""
        if parsed.hostname.lower() == "youtu.be" and len(parts) == 1:
            video_id = parts[0]
        elif len(parts) == 2 and parts[0] in {"shorts", "live", "embed", "v", "e"}:
            video_id = parts[1]
        elif parsed.path.rstrip("/") == "/watch":
            video_id = dict(parse_qsl(parsed.query)).get("v", "")
        if re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            return f"https://www.youtube.com/watch?v={video_id}"
    except ValueError:
        pass
    return ""


def remover_playlist_da_url(url):
    if not url_do_youtube(url):
        return url
    parsed = urlparse(url)
    parametros = [
        (chave, valor)
        for chave, valor in parse_qsl(parsed.query, keep_blank_values=True)
        if chave != "list"
    ]
    return urlunparse(parsed._replace(query=urlencode(parametros)))


def converter_tempo_para_segundos(valor, nome_campo):
    texto = str(valor).strip().replace(",", ".")
    if not texto:
        raise ValueError(f"Informe o tempo {nome_campo} do GIF.")

    partes = texto.split(":")
    if len(partes) not in (1, 2, 3) or any(not parte for parte in partes):
        raise ValueError(
            f"Tempo {nome_campo} inválido. Use segundos, mm:ss ou hh:mm:ss."
        )

    try:
        if len(partes) == 1:
            total = float(partes[0])
        else:
            if any(not parte.isdigit() for parte in partes[:-1]):
                raise ValueError
            segundos = float(partes[-1])
            if segundos >= 60:
                raise ValueError
            minutos = int(partes[-2])
            if len(partes) == 3 and minutos >= 60:
                raise ValueError
            horas = int(partes[0]) if len(partes) == 3 else 0
            total = horas * 3600 + minutos * 60 + segundos
    except ValueError:
        raise ValueError(
            f"Tempo {nome_campo} inválido. Use segundos, mm:ss ou hh:mm:ss."
        ) from None

    if not math.isfinite(total):
        raise ValueError(
            f"Tempo {nome_campo} inválido. Use segundos, mm:ss ou hh:mm:ss."
        )
    if total < 0:
        raise ValueError(f"O tempo {nome_campo} do GIF não pode ser negativo.")
    return total


def validar_intervalo_gif(inicio, fim):
    inicio_segundos = converter_tempo_para_segundos(inicio, "inicial")
    fim_segundos = converter_tempo_para_segundos(fim, "final")
    if fim_segundos <= inicio_segundos:
        raise ValueError("O tempo final do GIF deve ser maior que o tempo inicial.")
    if fim_segundos - inicio_segundos > DURACAO_MAXIMA_GIF:
        raise ValueError(
            f"O trecho do GIF pode ter no máximo {DURACAO_MAXIMA_GIF} segundos."
        )
    return inicio_segundos, fim_segundos


def limpar_mensagem_erro(erro):
    texto = re.sub(r"\x1b\[[0-9;]*m", "", str(erro))
    return texto.replace("\r", "").strip()


def erro_http_403(erro):
    return "HTTP Error 403" in limpar_mensagem_erro(erro)


def opcoes_base(
    progress_hook=None,
    postprocessor_hook=None,
    playlist=False,
    silencioso=False,
    cookies=True,
):
    opcoes = {
        "noplaylist": not playlist,
        "quiet": silencioso,
        "continuedl": False,
        "retries": 5,
        "fragment_retries": 5,
        "file_access_retries": 3,
        "extractor_retries": 3,
        "no_color": True,
    }
    if progress_hook:
        opcoes["progress_hooks"] = [progress_hook]
    if postprocessor_hook:
        opcoes["postprocessor_hooks"] = [postprocessor_hook]
    ffmpeg = caminho_ffmpeg()
    if ffmpeg is not None:
        opcoes["ffmpeg_location"] = str(ffmpeg.parent)
        diretorio_ffmpeg = str(ffmpeg.parent)
        entradas_path = os.environ.get("PATH", "").split(os.pathsep)
        if diretorio_ffmpeg.casefold() not in {
            entrada.casefold() for entrada in entradas_path if entrada
        }:
            os.environ["PATH"] = os.pathsep.join(
                [diretorio_ffmpeg, *entradas_path]
            )
    arquivo_cookies = caminho_cookies() if cookies else None
    if arquivo_cookies is not None:
        opcoes["cookiefile"] = str(arquivo_cookies)
    deno = caminho_ferramenta("deno")
    if deno is not None:
        opcoes["js_runtimes"] = {"deno": {"path": str(deno)}}
    return opcoes


def contar_videos_playlist(url):
    opcoes = opcoes_base(playlist=True, silencioso=True)
    opcoes["extract_flat"] = "in_playlist"
    with YoutubeDL(opcoes) as ydl_temp:
        info_playlist = ydl_temp.extract_info(url, download=False)
    entradas = info_playlist.get("entries") or []
    return info_playlist.get("playlist_count") or len(entradas)


def criar_opcoes_download(
    formato,
    caminho,
    progress_hook,
    playlist,
    inicio_gif=None,
    fim_gif=None,
    postprocessor_hook=None,
    post_metadata=None,
    selected_video=None,
):
    pasta_destino = Path(caminho)
    opcoes = opcoes_base(
        progress_hook=progress_hook,
        postprocessor_hook=postprocessor_hook,
        playlist=playlist,
    )
    opcoes["outtmpl"] = str(pasta_destino / "%(title)s.%(ext)s")
    if formato in {"mp3", "wav"}:
        opcoes.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": formato,
                "preferredquality": "192" if formato == "mp3" else "0",
            }],
        })
    elif formato in {"mp4", "mp4_android_vr", "mp4_compat", "mkv"}:
        container = "mkv" if formato == "mkv" else "mp4"
        remuxer = POS_PROCESSADOR_MKV if container == "mkv" else POS_PROCESSADOR_MP4
        opcoes.update({
            "format": "best[ext=mp4]/best" if formato == "mp4_compat" else FORMATO_MELHOR_QUALIDADE,
            "merge_output_format": container,
            "postprocessors": [remuxer.copy()],
        })
        if formato == "mp4_android_vr":
            opcoes["extractor_args"] = {"youtube": {"player_client": ["android_vr"]}}
    elif formato == "webm":
        opcoes.update({
            "format": "bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/bestvideo*+bestaudio/best",
            "merge_output_format": "webm/mp4/mkv",
            "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "webm"}],
            "postprocessor_args": {"videoconvertor+ffmpeg_o": [
                "-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0", "-cpu-used", "4",
                "-c:a", "libopus"]},
        })
    elif formato == "gif":
        inicio_gif, fim_gif = validar_intervalo_gif(inicio_gif, fim_gif)
        if download_range_func is None:
            raise RuntimeError("O yt-dlp instalado não oferece suporte a recortes por tempo.")
        opcoes.update({
            "format": "bestvideo[height<=720]/bestvideo/best",
            "download_ranges": download_range_func([], [(inicio_gif, fim_gif)]),
            "postprocessors": [{
                "key": "FFmpegVideoConvertor",
                "preferedformat": "gif",
            }],
            "postprocessor_args": {
                "videoconvertor+ffmpeg_o": [
                    "-vf", FILTRO_GIF,
                    "-an",
                    "-loop", "0",
                ],
            },
        })
    else:
        raise ValueError(f"Formato de saída não suportado: {formato}")
    if formato in {"mp4", "mp4_android_vr", "mp4_compat", "mkv"}:
        # JPEG also works with file managers that cannot read WebP artwork.
        # EmbedThumbnail removes the temporary image after attaching the cover.
        opcoes["writethumbnail"] = True
        opcoes["postprocessors"].extend([
            {"key": "FFmpegThumbnailsConvertor", "format": "jpg", "when": "before_dl"},
            {"key": "EmbedThumbnail", "already_have_thumbnail": False},
        ])
    if post_metadata:
        opcoes.update(selection_options(post_metadata, selected_video))
        opcoes.update(allowed_extractors=EXTRACTORS, match_filter=media_filter,
                      ignoreerrors=True if selected_video is None and len(post_metadata["videos"]) > 1 else False)
        opcoes["outtmpl"] = str(pasta_destino / "%(id)s-%(playlist_index|1)s-%(title).150B.%(ext)s")

    return opcoes


class DownloadWorker(QObject):
    progresso_atualizado = Signal(str, int, int)
    download_concluido = Signal()
    download_erro = Signal(str)
    status_atualizado = Signal(str)
    metadata_atualizada = Signal(dict)
    detalhes_atualizados = Signal(str)

    def __init__(
        self,
        url,
        caminho,
        formato,
        playlist,
        inicio_gif=None,
        fim_gif=None,
        post_metadata=None,
        selected_video=None,
    ):
        super().__init__()
        self.url = url
        self.caminho = caminho
        self.formato = formato
        self.playlist = playlist
        self.inicio_gif = inicio_gif
        self.fim_gif = fim_gif
        self.post_metadata = post_metadata
        self.selected_video = selected_video
        self.saved_files = set()
        self._cancelado = False

    def cancelar(self):
        self._cancelado = True

    def run(self):
        total_videos = len(self.post_metadata["videos"]) if self.post_metadata else 0
        self.status_atualizado.emit("Iniciando download...")
        self.progresso_atualizado.emit("Iniciando download...", 0, 100)

        try:
            verificar_dependencias()
            if self.playlist:
                self.status_atualizado.emit("Lendo playlist...")
                self.progresso_atualizado.emit("Lendo playlist...", 0, 100)
                total_videos = contar_videos_playlist(self.url)

            media_atual = None

            def hook(dados):
                nonlocal media_atual
                info = dados.get("info_dict") or {}
                identity = info.get("id") or info.get("webpage_url") or info.get("title")
                if identity and identity != media_atual:
                    media_atual = identity
                    self.metadata_atualizada.emit({"title": info.get("title"),
                                                   "thumbnail": info.get("thumbnail")})
                total_bytes = dados.get("total_bytes") or dados.get("total_bytes_estimate") or 0
                downloaded = dados.get("downloaded_bytes") or 0
                if total_bytes:
                    detalhe = f"{formatar_bytes(downloaded)} de {formatar_bytes(total_bytes)} · stream atual"
                    if dados.get("speed"):
                        detalhe += f" · {formatar_bytes(dados['speed'])}/s"
                    self.detalhes_atualizados.emit(detalhe)
                if self._cancelado:
                    raise Exception("Download cancelado pelo usuário")

                status = dados.get("status")

                prefixo = ""
                if self.playlist or (self.post_metadata and self.selected_video is None):
                    indice = dados.get("info_dict", {}).get("playlist_index")
                    if total_videos and indice:
                        valor = (next((n for n, item in enumerate(self.post_metadata["videos"], 1) if item["index"] == indice), indice)
                                 if self.post_metadata else min(indice, total_videos))
                        prefixo = f"Vídeo {valor} de {total_videos} · "
                    else:
                        prefixo = "Playlist · mídia atual · "

                if status == "downloading":
                    if total_bytes > 0:
                        porcentagem = downloaded / total_bytes * 100
                        texto = f"{prefixo}Baixando... {porcentagem:.1f}%"
                        self.progresso_atualizado.emit(texto, int(porcentagem), 100)
                    else:
                        self.progresso_atualizado.emit(f"{prefixo}Baixando…", 0, 0)
                elif status == "finished":
                    self.progresso_atualizado.emit("Finalizando e convertendo...", 100, 100)

            def hook_posprocessamento(dados):
                status = dados.get("status")
                if status == "started":
                    processador = dados.get("postprocessor", "")
                    if processador == "EmbedThumbnail":
                        mensagem = "Incorporando a capa original ao vídeo..."
                    elif processador == "ThumbnailsConvertor":
                        mensagem = "Preparando a capa original..."
                    else:
                        mensagem = (
                            "Reduzindo e convertendo o trecho para GIF..."
                            if self.formato == "gif"
                            else "Finalizando e convertendo..."
                        )
                    self.status_atualizado.emit(mensagem)
                    self.progresso_atualizado.emit(mensagem, 0, 0)
                elif status == "finished":
                    info = dados.get("info_dict") or {}
                    path = info.get("filepath")
                    if path and Path(path).suffix == "." + self.formato:
                        self.saved_files.add(path)
                    self.progresso_atualizado.emit("Finalizando...", 100, 100)

            try:
                opcoes = criar_opcoes_download(
                    self.formato,
                    self.caminho,
                    hook,
                    self.playlist,
                    self.inicio_gif,
                    self.fim_gif,
                    hook_posprocessamento,
                    self.post_metadata,
                    self.selected_video,
                )
                if self.formato == "gif":
                    mensagem = "Baixando e recortando o trecho do vídeo..."
                    self.status_atualizado.emit(mensagem)
                    self.progresso_atualizado.emit(mensagem, 0, 0)
                with YoutubeDL(opcoes) as ydl:
                    code = ydl.download([self.url])
                    if code:
                        count = sum(Path(path).is_file() for path in self.saved_files)
                        raise RuntimeError(f"Download parcial: {count} arquivo(s) salvo(s). Alguns vídeos do post falharam; os arquivos concluídos foram preservados.")
            except Exception as erro_download:
                if self.formato != "mp4" or not url_do_youtube(self.url) or not erro_http_403(erro_download):
                    raise

                tentativas_fallback = (
                    ("mp4_android_vr", "Alta qualidade bloqueada. Tentando outra rota sem limitar a resolução..."),
                    ("mp4_compat", "Alta qualidade indisponível. Tentando modo compatível..."),
                )

                for formato_fallback, mensagem in tentativas_fallback:
                    self.status_atualizado.emit(mensagem)
                    self.progresso_atualizado.emit(mensagem, 0, 100)
                    try:
                        opcoes = criar_opcoes_download(
                            formato_fallback,
                            self.caminho,
                            hook,
                            self.playlist,
                            postprocessor_hook=hook_posprocessamento,
                        )
                        with YoutubeDL(opcoes) as ydl:
                            ydl.download([self.url])
                        break
                    except Exception as erro_fallback:
                        if formato_fallback == "mp4_compat" or not erro_http_403(erro_fallback):
                            raise

            self.download_concluido.emit()
        except Exception as erro:
            source = classify_url(self.url)
            message = limpar_mensagem_erro(erro)
            self.download_erro.emit(message if message.startswith("Download parcial:") else
                                    friendly_error(erro, source["name"] if source else "essa fonte"))


THEMES = {
    "escuro": dict(bg="#10151f", glow="#22354c", panel="#1c2736", field="#152131",
                   text="#f4f7fb", muted="#b4c3d5", border="#40536c", accent="#4d9cff",
                   selected="#203f64", track="#354963", error="#ffaaaa"),
    "claro": dict(bg="#f4f6fa", glow="#dfebf9", panel="#fafcff", field="#ffffff",
                  text="#18212d", muted="#526277", border="#b8cbe3", accent="#0066cc",
                  selected="#e4f0ff", track="#d7e3f2", error="#a52132"),
}


def formatar_bytes(valor):
    valor = max(0, valor or 0)
    for unidade in ("B", "KB", "MB", "GB"):
        if valor < 1024 or unidade == "GB":
            return f"{valor:.1f} {unidade}" if unidade != "B" else f"{int(valor)} B"
        valor /= 1024


def icone_download(tamanho=64):
    pixmap = QPixmap(tamanho, tamanho)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(tamanho / 64, tamanho / 64)
    painter.setBrush(QColor("#203751"))
    painter.setPen(QPen(QColor("#56728f"), 1))
    painter.drawRoundedRect(QRectF(2, 2, 60, 60), 14, 14)
    painter.setPen(QPen(QColor("#b4d5ff"), 3, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.drawLine(QPointF(32, 15), QPointF(32, 39))
    painter.drawPolyline(QPolygonF([QPointF(23, 31), QPointF(32, 40), QPointF(41, 31)]))
    painter.drawPolyline(QPolygonF([QPointF(17, 39), QPointF(17, 49),
                                   QPointF(47, 49), QPointF(47, 39)]))
    painter.end()
    return QIcon(pixmap)


class FormatPicker(QFrame):
    currentTextChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._index = 0
        self._columns = 0
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(8)
        self._group = QButtonGroup(self)
        self.buttons = []
        for index, (label, value) in enumerate(FORMATOS_SAIDA.items()):
            button = QPushButton(value.upper())
            button.setCheckable(True)
            button.setProperty("format", True)
            button.setMinimumHeight(48)
            button.setMinimumWidth(62)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            button.setAccessibleName(label)
            button.setToolTip(label)
            self._group.addButton(button, index)
            self.buttons.append(button)
        self.buttons[0].setChecked(True)
        self._group.idClicked.connect(self.setCurrentIndex)
        self._arrange(3)

    def _arrange(self, columns):
        if columns == self._columns:
            return
        self._columns = columns
        for index, button in enumerate(self.buttons):
            self._grid.addWidget(button, index // columns, index % columns)
        for column in range(6):
            self._grid.setColumnStretch(column, 1 if column < columns else 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._arrange(6 if self.width() >= 540 else 3)

    def currentText(self):
        return list(FORMATOS_SAIDA)[self._index]

    def currentIndex(self):
        return self._index

    def count(self):
        return len(self.buttons)

    def setCurrentIndex(self, index):
        if 0 <= index < self.count():
            changed = index != self._index
            self._index = index
            self.buttons[index].setChecked(True)
            if changed:
                self.currentTextChanged.emit(self.currentText())


class PlaylistCheckBox(QCheckBox):
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.isChecked():
            option = QStyleOptionButton()
            self.initStyleOption(option)
            rect = self.style().subElementRect(QStyle.SubElement.SE_CheckBoxIndicator, option, self)
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor("#ffffff"), 2, Qt.PenStyle.SolidLine,
                                Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            painter.drawPolyline(QPolygonF([QPointF(rect.left() + 5, rect.top() + 10),
                                            QPointF(rect.left() + 9, rect.top() + 14),
                                            QPointF(rect.left() + 16, rect.top() + 6)]))
            painter.end()


class Thumbnail(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("Thumbnail")
        self.setFixedSize(184, 104)
        self.pixmap = QPixmap()
        self.color = QColor("#b4c3d5")
        self.setAccessibleName("Miniatura da mídia")

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(self.rect()), 10, 10)
        painter.setClipPath(clip)
        if not self.pixmap.isNull():
            scaled = self.pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap((self.width() - scaled.width()) // 2,
                               (self.height() - scaled.height()) // 2, scaled)
        else:
            painter.setPen(QPen(self.color, 2))
            painter.drawRoundedRect(QRectF(69, 32, 46, 36), 4, 4)
            painter.drawEllipse(QPointF(102, 42), 4, 4)
            painter.drawPolyline(QPolygonF([QPointF(72, 62), QPointF(85, 48),
                                           QPointF(95, 59), QPointF(103, 53), QPointF(112, 63)]))
        painter.end()


class FundoMidia(QWidget):
    """Cached artwork behind the scroll area; controls are never blurred."""
    imagem_alterada = Signal(bool)
    MAX_DIMENSION = 640
    BLUR_RADIUS = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self._imagem = QPixmap()
        self._tema = "escuro"
        self._intensidade = 0.0
        self._animacao = QPropertyAnimation(self, b"intensidade", self)
        self._animacao.setDuration(250)
        self._animacao.setEasingCurve(QEasingCurve.Type.OutCubic)

    @Property(float)
    def intensidade(self):
        return self._intensidade

    @intensidade.setter
    def intensidade(self, value):
        self._intensidade = value
        self.update()

    def tem_imagem(self):
        return not self._imagem.isNull()

    def definir_tema(self, theme):
        self._tema = theme
        self.update()

    @staticmethod
    def preparar_imagem(image):
        if image.isNull():
            return QPixmap()
        reduced = image
        if max(image.width(), image.height()) > FundoMidia.MAX_DIMENSION:
            reduced = image.scaled(640, 640, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
        # Extend edge pixels so the blur cannot introduce a transparent border.
        pad = FundoMidia.BLUR_RADIUS * 4
        w, h = reduced.width(), reduced.height()
        padded = QImage(w + pad * 2, h + pad * 2, QImage.Format.Format_ARGB32_Premultiplied)
        padded.fill(Qt.GlobalColor.transparent)
        painter = QPainter(padded)
        for left, width, source_left, source_width in [(0, pad, 0, 1), (pad, w, 0, w), (pad + w, pad, w - 1, 1)]:
            for top, height, source_top, source_height in [(0, pad, 0, 1), (pad, h, 0, h), (pad + h, pad, h - 1, 1)]:
                painter.drawImage(QRectF(left, top, width, height), reduced,
                                  QRectF(source_left, source_top, source_width, source_height))
        painter.end()
        scene = QGraphicsScene()
        item = scene.addPixmap(QPixmap.fromImage(padded))
        effect = QGraphicsBlurEffect()
        effect.setBlurRadius(FundoMidia.BLUR_RADIUS)
        effect.setBlurHints(QGraphicsBlurEffect.BlurHint.PerformanceHint)
        item.setGraphicsEffect(effect)
        result = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
        result.fill(Qt.GlobalColor.transparent)
        painter = QPainter(result)
        scene.render(painter, QRectF(result.rect()), QRectF(pad, pad, w, h))
        painter.end()
        if not reduced.hasAlphaChannel():
            result = result.convertToFormat(QImage.Format.Format_RGB32)
        return QPixmap.fromImage(result)

    def definir_imagem(self, image):
        try:
            prepared = self.preparar_imagem(image)
        except Exception:
            prepared = QPixmap()  # Optional decoration never fails the download.
        if prepared.isNull():
            self.limpar()
            return
        was_active = self.tem_imagem()
        self._animacao.stop()
        self._imagem = prepared
        self.intensidade = 0.0
        if not was_active:
            self.imagem_alterada.emit(True)
        self._animacao.setStartValue(0.0)
        self._animacao.setEndValue(1.0)
        self._animacao.start()

    def limpar(self):
        was_active = self.tem_imagem()
        self._animacao.stop()
        self._imagem = QPixmap()
        self.intensidade = 0.0
        if was_active:
            self.imagem_alterada.emit(False)

    def paintEvent(self, event):
        painter = QPainter(self)
        colors = THEMES[self._tema]
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        for position, key in [(0, "bg"), (.55, "glow"), (1, "bg")]:
            gradient.setColorAt(position, QColor(colors[key]))
        painter.fillRect(self.rect(), gradient)
        if self.tem_imagem():
            factor = max(self.width() / self._imagem.width(), self.height() / self._imagem.height())
            width, height = self._imagem.width() * factor, self._imagem.height() * factor
            target = QRectF((self.width() - width) / 2, (self.height() - height) / 2, width, height)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.setOpacity(self._intensidade)
            painter.drawPixmap(target, self._imagem, QRectF(self._imagem.rect()))
            painter.setOpacity(1)
            overlay = QLinearGradient(0, 0, self.width(), self.height())
            for position, key in [(0, "bg"), (.55, "glow"), (1, "bg")]:
                color = QColor(colors[key])
                color.setAlphaF(.68 if self._tema == "escuro" else .78)
                overlay.setColorAt(position, color)
            painter.fillRect(self.rect(), overlay)
        painter.end()


class JanelaPrincipal(QMainWindow):
    MAX_THUMBNAIL_BYTES = 8 * 1024 * 1024
    MAX_PREVIEW_BYTES = 128 * 1024

    def __init__(self, configuracoes=None):
        super().__init__()
        self.setWindowTitle("UIfor_yt-dlp")
        self.setWindowIcon(icone_download())
        available = QApplication.primaryScreen().availableGeometry()
        # Leave room for native decorations at high DPI or on a smaller monitor.
        self.setMinimumSize(min(720, available.width() - 32), min(540, available.height() - 40))
        self.settings = configuracoes or QSettings("UIfor_yt-dlp", "UIfor_yt-dlp")
        self.tema = self.settings.value("appearance/theme", "escuro")
        if self.tema not in THEMES:
            self.tema = "escuro"
        self.pasta_selecionada = ""
        self.worker_thread = None
        self.worker = None
        self._working = False
        self._thumbnail_url = ""
        self._thumbnail_reply = None
        self._preview_target = ""
        self._preview_loaded = False
        self._preview_reply = None
        self._preview_job = None
        self._post_metadata = None
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(450)
        self._preview_timer.timeout.connect(self._buscar_previa)
        self._network = QNetworkAccessManager(self)
        self._setup_ui()
        self.input_url.textChanged.connect(self._agendar_previa)
        self._aplicar_tema(self.tema)
        self.resize(min(1180, available.width() - 32), min(780, available.height() - 40))
        geometry = self.settings.value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        self._maximizar_ao_abrir = self.settings.value("window/maximized", True, type=bool)

    def mostrar(self):
        if self._maximizar_ao_abrir:
            self.showMaximized()
        else:
            self.show()

    def _label(self, text, role=None):
        label = QLabel(text)
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setWordWrap(True)
        if role:
            label.setObjectName(role)
        return label

    def _button(self, text, callback=None, primary=False):
        button = QPushButton(text)
        button.setMinimumHeight(48)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        if primary:
            button.setProperty("primary", True)
        if callback:
            button.clicked.connect(callback)
        return button

    def _input(self, placeholder, name):
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setMinimumHeight(48)
        field.setAccessibleName(name)
        return field

    def _panel(self):
        panel = QFrame()
        panel.setObjectName("Panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        return panel, layout

    def _setup_ui(self):
        self.fundo = FundoMidia()
        background_layout = QVBoxLayout(self.fundo)
        background_layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(self.fundo)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.viewport().setObjectName("MediaViewport")
        self.scroll_area.viewport().setAutoFillBackground(False)
        background_layout.addWidget(self.scroll_area)
        canvas = QWidget()
        canvas.setObjectName("Canvas")
        self.scroll_area.setWidget(canvas)
        self._outer = QHBoxLayout(canvas)
        self._outer.setContentsMargins(32, 24, 32, 24)
        content = QWidget()
        content.setMaximumWidth(1560)
        self._outer.addStretch()
        self._outer.addWidget(content, 1)
        self._outer.addStretch()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)
        self._legendas_fundo = []

        def artwork_caption(text):
            label = self._label(text, "Muted")
            self._legendas_fundo.append(label)
            return label

        header = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(icone_download().pixmap(52, 52))
        icon.setFixedSize(52, 52)
        header.addWidget(icon)
        brand = QVBoxLayout()
        brand.setSpacing(4)
        self._titulo = self._label("UIfor_yt-dlp", "Brand")
        brand.addWidget(self._titulo)
        brand.addWidget(artwork_caption("Vídeos, áudio e GIFs"))
        header.addLayout(brand)
        header.addStretch()
        self.theme_buttons = {}
        group = QButtonGroup(self)
        for key, text in (("claro", "Claro"), ("escuro", "Escuro")):
            button = self._button(text, lambda checked=False, theme=key: self._aplicar_tema(theme))
            button.setCheckable(True)
            button.setProperty("theme", True)
            button.setAccessibleName(f"Tema {key}")
            group.addButton(button)
            self.theme_buttons[key] = button
            header.addWidget(button)
        self.btn_sobre = self._button("Sobre", self._mostrar_sobre)
        header.addWidget(self.btn_sobre)
        layout.addLayout(header)
        heading = QVBoxLayout()
        heading.setSpacing(4)
        heading.addWidget(self._label("Novo download", "Heading"))
        heading.addWidget(artwork_caption("Cole um link e escolha como salvar."))
        layout.addLayout(heading)

        self._columns = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._columns.setSpacing(24)
        self._form, form = self._panel()
        form.addWidget(self._label("Link da mídia", "FieldLabel"))
        url_row = QHBoxLayout()
        self.input_url = self._input("Cole o link aqui", "Link da mídia")
        self.btn_colar = self._button("Colar", self._colar)
        url_row.addWidget(self.input_url, 1)
        url_row.addWidget(self.btn_colar)
        form.addLayout(url_row)
        self.label_fonte = self._label(SOURCE_HELP, "Muted")
        form.addWidget(self.label_fonte)
        self._post_box = QWidget()
        post_layout = QVBoxLayout(self._post_box)
        post_layout.setContentsMargins(0, 0, 0, 0)
        post_layout.addWidget(self._label("Vídeos deste post", "FieldLabel"))
        self.combo_post = QComboBox()
        self.combo_post.setMinimumHeight(48)
        self.combo_post.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.combo_post.setMinimumContentsLength(16)
        self.combo_post.setMinimumWidth(0)
        self.combo_post.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.combo_post.setMaxVisibleItems(10)
        self.combo_post.setAccessibleName("Vídeos deste post")
        self.combo_post.currentIndexChanged.connect(self._selecionar_video_post)
        post_layout.addWidget(self.combo_post)
        self._post_box.hide()
        form.addWidget(self._post_box)
        form.addWidget(self._label("Formato de saída", "FieldLabel"))
        self.combo_formato = FormatPicker()
        form.addWidget(self.combo_formato)
        self.label_qualidade = self._label("Melhor qualidade disponível", "Muted")
        form.addWidget(self.label_qualidade)

        self._opcoes_gif = QWidget()
        gif_layout = QVBoxLayout(self._opcoes_gif)
        gif_layout.setContentsMargins(0, 0, 0, 0)
        gif_layout.setSpacing(8)
        gif_layout.addWidget(self._label("Intervalo do GIF", "FieldLabel"))
        gif_row = QHBoxLayout()
        self.input_gif_inicio = self._input("00:01", "Início do GIF")
        self.input_gif_fim = self._input("00:03", "Fim do GIF")
        for text, field in (("Início", self.input_gif_inicio), ("Fim", self.input_gif_fim)):
            column = QVBoxLayout()
            column.addWidget(self._label(text, "Muted"))
            column.addWidget(field)
            gif_row.addLayout(column, 1)
        gif_layout.addLayout(gif_row)
        gif_layout.addWidget(self._label("Trecho de até 30 segundos", "Muted"))
        form.addWidget(self._opcoes_gif)
        form.addWidget(self._label("Pasta de destino", "FieldLabel"))
        folder_row = QHBoxLayout()
        self.label_pasta = self._input("Selecione uma pasta", "Pasta de destino")
        self.label_pasta.setReadOnly(True)
        self.btn_pasta = self._button("Alterar", self._escolher_pasta)
        folder_row.addWidget(self.label_pasta, 1)
        folder_row.addWidget(self.btn_pasta)
        form.addLayout(folder_row)
        self.check_playlist = PlaylistCheckBox("Baixar playlist")
        self.check_playlist.setMinimumHeight(32)
        self.check_playlist.setToolTip("Quando o link incluir uma lista")
        form.addWidget(self.check_playlist)
        self.btn_baixar = self._button("Baixar vídeo", self._iniciar_download, primary=True)
        form.addWidget(self.btn_baixar)
        self._columns.addWidget(self._form, 3)

        self._status_panel, status = self._panel()
        self.label_andamento = self._label("Aguardando um download", "SectionTitle")
        status.addWidget(self.label_andamento)
        self.thumbnail = Thumbnail()
        status.addWidget(self.thumbnail)
        self.label_midia = self._label("A mídia aparecerá aqui", "MediaTitle")
        self.label_midia.setMinimumWidth(180)
        status.addWidget(self.label_midia)
        self.label_formato = self._label("MP4 · Vídeo", "Muted")
        status.addWidget(self.label_formato)
        self.label_percentual = self._label("0%", "Percentage")
        status.addWidget(self.label_percentual)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setAccessibleName("Progresso do download")
        status.addWidget(self.progress_bar)
        self.label_status = self._label("Aguardando", "Muted")
        self.label_detalhes = self._label("", "Muted")
        status.addWidget(self.label_status)
        status.addWidget(self.label_detalhes)
        self.label_erro = self._label("", "Error")
        self.label_erro.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.label_erro.hide()
        status.addWidget(self.label_erro)
        status.addStretch()
        self.label_ajuda = self._label("A conversão começa após o download.", "Muted")
        status.addWidget(self.label_ajuda)
        self.btn_abrir_pasta = self._button("Abrir pasta", self._abrir_pasta)
        self.btn_abrir_pasta.setEnabled(False)
        status.addWidget(self.btn_abrir_pasta)
        self._columns.addWidget(self._status_panel, 2)
        layout.addLayout(self._columns)
        layout.addStretch()
        footer = QHBoxLayout()
        footer.addWidget(artwork_caption("UIfor_yt-dlp · V3.3"))
        footer.addStretch()
        footer.addWidget(artwork_caption("Sobre · GPLv3"))
        layout.addLayout(footer)
        self.combo_formato.currentTextChanged.connect(self._atualizar_opcoes_formato)
        self._atualizar_opcoes_formato()
        self._atualizar_layout_responsivo()
        self.fundo.imagem_alterada.connect(self._atualizar_paineis)

    def _atualizar_paineis(self, active):
        for panel in (self._form, self._status_panel, *self._legendas_fundo):
            panel.setProperty("wallpaper", active)
            panel.style().unpolish(panel)
            panel.style().polish(panel)
            panel.update()

    def _aplicar_tema(self, theme):
        if theme not in THEMES:
            return
        self.tema = theme
        self.settings.setValue("appearance/theme", theme)
        c = THEMES[theme]
        self.fundo.definir_tema(theme)
        panel_color = QColor(c["panel"])
        glass_panel = f"rgba({panel_color.red()}, {panel_color.green()}, {panel_color.blue()}, 214)"
        palette = QPalette()
        for role, color in ((QPalette.ColorRole.Window, c["bg"]),
                            (QPalette.ColorRole.WindowText, c["text"]),
                            (QPalette.ColorRole.Base, c["field"]),
                            (QPalette.ColorRole.AlternateBase, c["panel"]),
                            (QPalette.ColorRole.Text, c["text"]),
                            (QPalette.ColorRole.Button, c["panel"]),
                            (QPalette.ColorRole.ButtonText, c["text"]),
                            (QPalette.ColorRole.Highlight, c["accent"]),
                            (QPalette.ColorRole.HighlightedText, "#10151f" if theme == "escuro" else "#ffffff")):
            palette.setColor(role, QColor(color))
        self.setPalette(palette)
        for key, button in self.theme_buttons.items():
            button.setChecked(key == theme)
        self.thumbnail.color = QColor(c["muted"])
        self.thumbnail.update()
        self.setStyleSheet(f"""
            QMainWindow {{ background: {c['bg']}; }}
            QScrollArea, QWidget#Canvas, QWidget#MediaViewport {{ background: transparent; }}
            QWidget {{ color: {c['text']}; font-size: 14px; }}
            QLabel {{ background: transparent; }}
            QLabel#Brand {{ font-size: 28px; font-weight: 600; }}
            QLabel#Heading {{ font-size: 30px; font-weight: 600; }}
            QLabel#SectionTitle {{ font-size: 22px; font-weight: 600; }}
            QLabel#FieldLabel, QLabel#MediaTitle {{ font-size: 15px; font-weight: 600; }}
            QLabel#Percentage {{ font-size: 30px; font-weight: 600; }}
            QLabel#Muted {{ color: {c['muted']}; font-size: 13px; }}
            QLabel#Muted[wallpaper="true"] {{ color: {'#ffffff' if theme == 'escuro' else c['text']}; }}
            QLabel#Error {{ color: {c['error']}; }}
            QFrame#Panel {{ background: {c['panel']}; border: 1px solid {c['border']};
                            border-radius: 18px; }}
            QFrame#Panel[wallpaper="true"] {{ background: {glass_panel}; }}
            QFrame#Thumbnail {{ background: {c['field']}; border-radius: 10px; }}
            QLineEdit, QComboBox {{ background: {c['field']}; color: {c['text']};
                         border: 1px solid {c['border']}; border-radius: 9px; padding: 0 14px; }}
            QLineEdit:focus, QComboBox:focus {{ border: 2px solid {c['accent']}; }}
            QPushButton {{ background: {c['field']}; color: {c['text']};
                           border: 1px solid {c['border']}; border-radius: 9px; padding: 8px 14px; }}
            QPushButton:hover {{ border-color: {c['accent']}; background: {c['selected']}; }}
            QPushButton:focus {{ border: 2px solid {c['accent']}; }}
            QPushButton:checked {{ border: 2px solid {c['accent']}; background: {c['selected']}; }}
            QPushButton[primary="true"] {{ background: {c['accent']}; color: {'#10151f' if theme == 'escuro' else '#ffffff'};
                font-weight: 600; border-color: {c['accent']}; }}
            QPushButton:disabled, QLineEdit:disabled {{ color: {c['muted']}; }}
            QPushButton[primary="true"]:disabled {{ background: {c['selected']}; color: {c['muted']}; }}
            QCheckBox {{ spacing: 10px; background: transparent; }}
            QCheckBox::indicator {{ width: 20px; height: 20px; background: {c['field']};
                                   border: 1px solid {c['border']}; border-radius: 4px; }}
            QCheckBox::indicator:checked {{ background: {c['accent']}; border-color: {c['accent']}; }}
            QCheckBox::indicator:focus {{ border: 2px solid {c['accent']}; }}
            QProgressBar {{ background: {c['track']}; border: none; border-radius: 6px; }}
            QProgressBar::chunk {{ background: {c['accent']}; border-radius: 6px; }}
            QScrollBar:vertical {{ width: 10px; background: {c['bg']}; }}
            QScrollBar::handle:vertical {{ background: {c['border']}; min-height: 24px; border-radius: 5px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QToolTip {{ color: {c['text']}; background: {c['panel']}; border: 1px solid {c['border']}; }}
        """)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_columns"):
            self._atualizar_layout_responsivo()

    def _atualizar_layout_responsivo(self):
        wide = self.width() - 64 >= 1000
        direction = QBoxLayout.Direction.LeftToRight if wide else QBoxLayout.Direction.TopToBottom
        self._columns.setDirection(direction)
        self._columns.setStretch(0, 3 if wide else 0)
        self._columns.setStretch(1, 2 if wide else 0)
        margin = 32 if wide else 20
        self._outer.setContentsMargins(margin, 24, margin, 24)

    def _mostrar_sobre(self):
        box = QMessageBox(self)
        box.setWindowTitle("Sobre UIfor_yt-dlp")
        box.setTextFormat(Qt.TextFormat.PlainText)
        box.setText("UIfor_yt-dlp · V3.3\nVídeos, áudio e GIFs\n\nLicença GNU GPLv3. "
                    "Extração/download: yt-dlp. Conversão: FFmpeg. Interface: PySide6/Qt.\n\n"
                    "O projeto começou fechado e sem IA. Modelos, principalmente da OpenAI, "
                    "foram usados inicialmente como experimento e se tornaram a principal forma "
                    "de desenvolvimento e manutenção, com orientação humana e pouca edição direta. "
                    "A primeira versão pública é a v3.\n\n"
                    "Essa descrição se refere ao código deste aplicativo. As dependências mantêm "
                    "sua própria autoria. Nenhum modelo de IA executa os downloads.\n\n"
                    "Fontes integradas: " + SOURCE_HELP + ".\nLinks públicos individuais; playlists do YouTube. A disponibilidade depende do site e do link.")
        box.exec()

    def _colar(self):
        self.input_url.setText(QApplication.clipboard().text().strip())
        self.input_url.setFocus()

    def _escolher_pasta(self):
        folder = QFileDialog.getExistingDirectory(self, "Pasta de destino", self.pasta_selecionada)
        if folder:
            self.pasta_selecionada = folder
            self.label_pasta.setText(folder)
            self.label_pasta.setToolTip(folder)

    def _abrir_pasta(self):
        if self.pasta_selecionada and Path(self.pasta_selecionada).is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.pasta_selecionada))

    def _formato_selecionado(self):
        return FORMATOS_SAIDA[self.combo_formato.currentText()]

    def _texto_botao_formato(self, formato):
        if formato == "gif":
            return "Gerar GIF"
        return "Extrair áudio" if formato in {"mp3", "wav"} else "Baixar vídeo"

    def _mensagens_resultado(self, formato):
        if formato == "gif":
            return "GIF gerado com sucesso!", "Falha ao gerar o GIF"
        if formato in {"mp3", "wav"}:
            return "Áudio salvo com sucesso!", "Falha ao extrair o áudio"
        return "Vídeo salvo com sucesso!", "Falha ao baixar o vídeo"

    def _atualizar_opcoes_formato(self):
        formato = self._formato_selecionado()
        self._opcoes_gif.setVisible(formato == "gif")
        kind = "Áudio" if formato in {"mp3", "wav"} else "Animação" if formato == "gif" else "Vídeo"
        self.label_formato.setText(f"{formato.upper()} · {kind}")
        self.label_qualidade.setText("Trecho convertido em animação" if formato == "gif" else
                                    "Extração de áudio" if kind == "Áudio" else "WEBM: conversão quando necessária; pode demorar mais" if formato == "webm" else "Melhor qualidade disponível")
        if not self._working:
            self.btn_baixar.setText(self._texto_botao_formato(formato))

    def _set_working(self, working):
        self._working = working
        if working:
            self._cancelar_previa()
        for control in (self.input_url, self.btn_colar, self.combo_formato, self.btn_pasta,
                        self.input_gif_inicio, self.input_gif_fim, self.check_playlist, self.combo_post, self.btn_baixar):
            control.setEnabled(not working)
        if working:
            self.btn_baixar.setText("Processando…")
            self.btn_abrir_pasta.setEnabled(False)
        else:
            self._atualizar_opcoes_formato()

    def _erro_validacao(self, message, control):
        self.label_erro.setText(message)
        self.label_erro.show()
        control.setFocus()

    def _iniciar_download(self):
        if self._working or (self.worker_thread and self.worker_thread.isRunning()):
            return
        url = normalizar_url(self.input_url.text())
        formato = self._formato_selecionado()
        inicio_gif = fim_gif = None
        self.label_erro.hide()
        source = classify_url(url)
        if not source:
            self._erro_validacao("Informe um link de vídeo de uma das fontes aceitas. Perfis, stories e outras fontes ficam para uma próxima etapa.", self.input_url)
            return
        if not self.pasta_selecionada:
            self._erro_validacao("Selecione uma pasta de destino.", self.btn_pasta)
            return
        if formato == "gif":
            try:
                inicio_gif, fim_gif = validar_intervalo_gif(self.input_gif_inicio.text(), self.input_gif_fim.text())
            except ValueError as error:
                self._erro_validacao(str(error), self.input_gif_inicio)
                return
        if source["id"] != "youtube" and self._post_metadata is None:
            self._consultar_post(url, explicit=True)
            return
        if self._post_metadata:
            url = self._post_metadata["url"]
        playlist = source["id"] == "youtube" and self._post_metadata is None and self.check_playlist.isChecked() and url_tem_playlist(url)
        if source["id"] == "youtube" and self._post_metadata is None and url_tem_playlist(url) and not playlist:
            answer = QMessageBox.question(self, "Playlist detectada", "Baixar todos os vídeos da playlist?",
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            playlist = answer == QMessageBox.StandardButton.Yes
        url_download = url if playlist else remover_playlist_da_url(url)
        self._set_working(True)
        if not self._preview_loaded:
            self._limpar_thumbnail()
            self.label_midia.setText("Lendo informações da mídia…")
        self.label_detalhes.clear()
        self.label_ajuda.setText("A conversão começa após o download.")
        self.label_andamento.setText("Download em andamento")
        self._atualizar_progresso("Preparando…", 0, 0)
        self.worker = DownloadWorker(url_download, self.pasta_selecionada, formato, playlist, inicio_gif, fim_gif,
                                     self._post_metadata, self.combo_post.currentData() if self._post_metadata else None)
        self.worker_thread = QThread(self)
        self.worker.moveToThread(self.worker_thread)
        self.worker.progresso_atualizado.connect(self._atualizar_progresso)
        self.worker.status_atualizado.connect(self._atualizar_status)
        self.worker.metadata_atualizada.connect(self._atualizar_metadata)
        self.worker.detalhes_atualizados.connect(self.label_detalhes.setText)
        self.worker.download_concluido.connect(self._download_sucesso)
        self.worker.download_erro.connect(self._download_erro)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.download_concluido.connect(self.worker_thread.quit)
        self.worker.download_erro.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self._limpar_worker)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def _limpar_worker(self):
        self.worker = None
        self.worker_thread = None

    def _atualizar_progresso(self, texto, valor, maximo):
        self.progress_bar.setRange(0, maximo)
        self.progress_bar.setValue(valor)
        self.label_status.setText(texto)
        self.label_percentual.setText(f"{min(100, int(valor / maximo * 100))}%" if maximo else "…")
        if self._working:
            self.btn_baixar.setText("Baixando…" if "Baixando" in texto else "Processando…")

    def _atualizar_status(self, texto):
        self.label_status.setText(texto)

    def _download_sucesso(self):
        formato = self.worker.formato if self.worker else self._formato_selecionado()
        mensagem, _ = self._mensagens_resultado(formato)
        self._atualizar_progresso(mensagem, 100, 100)
        self.label_andamento.setText("Download concluído")
        self.label_detalhes.setText("Resultado disponível na pasta de destino.")
        self.label_ajuda.setText("Você já pode iniciar outro download.")
        self._set_working(False)
        self.btn_abrir_pasta.setEnabled(bool(self.pasta_selecionada))

    def _download_erro(self, erro):
        formato = self.worker.formato if self.worker else self._formato_selecionado()
        _, mensagem = self._mensagens_resultado(formato)
        self._atualizar_progresso(mensagem, 0, 100)
        self.label_andamento.setText("Não foi possível concluir")
        self.label_detalhes.clear()
        self.label_ajuda.setText("Revise o link e tente novamente.")
        self.label_erro.setText(limpar_mensagem_erro(erro))
        self.label_erro.show()
        self._set_working(False)
        if self.worker and any(Path(path).is_file() for path in self.worker.saved_files):
            self.btn_abrir_pasta.setEnabled(True)

    def _cancelar_previa(self):
        self._preview_timer.stop()
        job = self._preview_job
        self._preview_job = None
        if job:
            job.cancel()
            job.deleteLater()
        reply = self._preview_reply
        self._preview_reply = None
        if reply is not None:
            reply.abort()

    def _agendar_previa(self):
        if self._working:
            return
        source = classify_url(self.input_url.text())
        target = (url_video_previa(self.input_url.text()) if source and source["id"] == "youtube"
                  else source["url"] if source else "")
        self.label_fonte.setText((source["name"] + (" · Experimental" if source["experimental"] else "") + " · Link público")
                                 if source else SOURCE_HELP)
        self.check_playlist.setVisible(not source or source["id"] == "youtube")
        if target == self._preview_target:
            return
        self._cancelar_previa()
        self._preview_target = target
        self._preview_loaded = False
        self._post_metadata = None
        self._post_box.hide()
        self.combo_post.clear()
        self._limpar_thumbnail()
        self.label_midia.setText("A mídia aparecerá aqui")
        if target:
            self._preview_timer.start()

    def _url_consulta_previa(self, target):
        return QUrl("https://www.youtube.com/oembed?" + urlencode({"url": target, "format": "json"}))

    def _buscar_previa(self):
        target = self._preview_target
        if self._working or not target:
            return
        source = classify_url(target)
        if source and source["id"] != "youtube":
            self._consultar_post(target)
            return
        request = QNetworkRequest(self._url_consulta_previa(target))
        request.setTransferTimeout(5000)
        request.setMaximumRedirectsAllowed(4)
        request.setRawHeader(b"Accept", b"application/json")
        reply = self._network.get(request)
        reply.setReadBufferSize(self.MAX_PREVIEW_BYTES + 1)
        self._preview_reply = reply
        deadline = QTimer(reply)
        deadline.setSingleShot(True)
        deadline.timeout.connect(reply.abort)
        deadline.start(6000)
        data = bytearray()

        def read():
            data.extend(bytes(reply.readAll()))
            if len(data) > self.MAX_PREVIEW_BYTES:
                reply.abort()

        def finish():
            deadline.stop()
            read()
            if reply is self._preview_reply:
                self._preview_reply = None
                if not self._working and target == self._preview_target and reply.error() == QNetworkReply.NetworkError.NoError and len(data) <= self.MAX_PREVIEW_BYTES:
                    try:
                        info = json.loads(bytes(data))
                        if isinstance(info, dict) and isinstance(info.get("title"), str) and info["title"].strip():
                            self._preview_loaded = True
                            thumbnail = info.get("thumbnail_url")
                            self._atualizar_metadata({"title": info["title"], "thumbnail": thumbnail if isinstance(thumbnail, str) else ""})
                    except (ValueError, UnicodeError):
                        pass  # A preview failure never changes download/error state.
            reply.deleteLater()

        reply.readyRead.connect(read)
        reply.finished.connect(finish)

    def _consultar_post(self, target, explicit=False):
        self._cancelar_previa()
        if explicit:
            self._set_working(True)
            self.label_status.setText("Lendo vídeos do post…")
        job = MetadataLookup(Path(__file__), target, 45000 if explicit else 12000, self)
        self._preview_job = job

        def complete(info=None, error=None):
            if job is not self._preview_job:
                return
            self._preview_job = None
            job.deleteLater()
            if explicit:
                self._set_working(False)
            elif self._working or target != self._preview_target:
                return
            if error:
                if explicit:
                    self._erro_validacao(error, self.input_url)
                return
            self._post_metadata = info
            source = classify_url(info["url"])
            if source:
                self.label_fonte.setText(source["name"] + (" · Experimental" if source["experimental"] else "") + " · Link público")
            videos = info["videos"]
            self.combo_post.blockSignals(True)
            self.combo_post.clear()
            self.combo_post.addItem(f"Todos os vídeos ({len(videos)})", None)
            for ordinal, video in enumerate(videos, 1):
                self.combo_post.addItem(f"Vídeo {ordinal} — {video['title']}", video["index"])
            self.combo_post.setCurrentIndex(0)
            self.combo_post.blockSignals(False)
            self._post_box.setVisible(len(videos) > 1)
            self._preview_loaded = True
            self._selecionar_video_post()
            if explicit:
                if len(videos) == 1:
                    self._iniciar_download()
                else:
                    self.label_status.setText("Escolha um vídeo ou todos e clique em Baixar.")

        job.finished.connect(lambda info: complete(info=info))
        job.failed.connect(lambda error: complete(error=error))
        job.start()

    def _selecionar_video_post(self):
        if not self._post_metadata:
            return
        selected = self.combo_post.currentData()
        videos = self._post_metadata["videos"]
        video = next((item for item in videos if item["index"] == selected), videos[0])
        self._atualizar_metadata(video)

    def _atualizar_metadata(self, info):
        title = str(info.get("title") or "Mídia em andamento")[:300]
        self.label_midia.setText(title)
        thumbnail = info.get("thumbnail") or ""
        if thumbnail == self._thumbnail_url:
            return
        self._limpar_thumbnail()
        self._thumbnail_url = thumbnail
        url = QUrl(thumbnail)
        if url.scheme() not in {"http", "https"} or not url.host():
            return
        request = QNetworkRequest(url)
        request.setTransferTimeout(6000)
        request.setMaximumRedirectsAllowed(4)
        request.setRawHeader(b"Accept", b"image/*")
        reply = self._network.get(request)
        self._thumbnail_reply = reply
        data = bytearray()

        def read():
            data.extend(bytes(reply.readAll()))
            if len(data) > self.MAX_THUMBNAIL_BYTES:
                reply.abort()

        def finish():
            read()
            if reply is self._thumbnail_reply:
                self._thumbnail_reply = None
                if reply.error() == QNetworkReply.NetworkError.NoError and len(data) <= self.MAX_THUMBNAIL_BYTES:
                    image = QImage.fromData(bytes(data))
                    if not image.isNull() and image.width() * image.height() <= 25_000_000:
                        self.thumbnail.pixmap = QPixmap.fromImage(image)
                        self.thumbnail.update()
                        self.fundo.definir_imagem(image)
            reply.deleteLater()

        reply.readyRead.connect(read)
        reply.finished.connect(finish)

    def _limpar_thumbnail(self):
        reply = self._thumbnail_reply
        self._thumbnail_reply = None
        if reply is not None:
            reply.abort()
        self._thumbnail_url = ""
        self.thumbnail.pixmap = QPixmap()
        self.thumbnail.update()
        self.fundo.limpar()

    def closeEvent(self, event):
        if self.worker_thread and self.worker_thread.isRunning():
            self.label_status.setText("Aguarde o download terminar antes de fechar o aplicativo.")
            event.ignore()
            return
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.setValue("window/maximized", self.isMaximized())
        self.settings.sync()
        self._cancelar_previa()
        self._limpar_thumbnail()
        event.accept()


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--media-info":
        return run_helper(sys.argv[2], sys.argv[3], opcoes_base(silencioso=True, cookies=False))
    app = QApplication(sys.argv)
    app.setApplicationName("UIfor_yt-dlp")
    app.setApplicationVersion("3.3")
    app.setOrganizationName("UIfor_yt-dlp")
    app.setStyle("Fusion")
    app.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont))
    janela = JanelaPrincipal()
    janela.mostrar()
    sys.exit(app.exec())


if __name__ == "__main__":
    sys.exit(main())
