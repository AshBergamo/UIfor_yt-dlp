import math
import os
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from PySide6.QtCore import (
    Qt, QThread, Signal, QObject, QPoint, QEvent
)
from PySide6.QtGui import (
    QIcon, QFont, QColor, QPainter, QPen, QBrush, QCursor
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QProgressBar,
    QFileDialog, QMessageBox, QFrame, QSizePolicy,
    QGraphicsDropShadowEffect, QScrollArea, QLayout, QBoxLayout
)

try:
    from yt_dlp import YoutubeDL
    from yt_dlp.utils import download_range_func
except ImportError:
    YoutubeDL = None
    download_range_func = None

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

COR_FUNDO = "#0f1115"
COR_CARD = "#1a1d23"
COR_CARD_HOVER = "#20242c"
COR_TEXTO = "#e8eaed"
COR_TEXTO_SUAVE = "#8b919a"
COR_TEXTO_MUTED = "#5a5f6a"
COR_BORDA = "#2d3139"
COR_VERMELHO = "#ff1f2d"
COR_VERMELHO_ESCURO = "#c8101f"
COR_VERMELHO_CLARO = "#3a1015"
COR_VERMELHO_GLOW = "#ff3b47"
COR_VERDE = "#00d47e"
COR_AMARELO = "#ffb300"
COR_ACENTO = COR_VERMELHO

RAIO_CARD = 16
RAIO_BOTAO = 12
RAIO_INPUT = 10
RAIO_PROGRESSO = 10
ALTURA_CONTROLE = 48
LARGURA_LIMITE_PASTA = 620

FONTE_TITULO = ("Segoe UI", 28, QFont.Weight.Bold)
FONTE_SUBTITULO = ("Segoe UI", 13, QFont.Weight.Medium)
FONTE_LABEL = ("Segoe UI", 11, QFont.Weight.DemiBold)
FONTE_TEXTO = ("Segoe UI", 11)
FONTE_PEQUENA = ("Segoe UI", 9)
FONTE_BOTAO = ("Segoe UI", 12, QFont.Weight.DemiBold)


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
    url = url.strip()
    if url and "://" not in url:
        url = f"https://{url}"
    return url


def url_do_youtube(url):
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return host in DOMINIOS_YOUTUBE or host.endswith(".youtube.com")


def url_tem_playlist(url):
    parametros = dict(parse_qsl(urlparse(url).query, keep_blank_values=True))
    return bool(parametros.get("list"))


def remover_playlist_da_url(url):
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
    cookies = caminho_cookies()
    if cookies is not None:
        opcoes["cookiefile"] = str(cookies)
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
):
    pasta_destino = Path(caminho)
    opcoes = opcoes_base(
        progress_hook=progress_hook,
        postprocessor_hook=postprocessor_hook,
        playlist=playlist,
    )
    if formato in {"mp3", "wav"}:
        opcoes.update({
            "format": "bestaudio/best",
            "outtmpl": str(pasta_destino / "%(title)s.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": formato,
                "preferredquality": "192" if formato == "mp3" else "0",
            }],
        })
    elif formato == "mp4":
        opcoes.update({
            "format": FORMATO_MELHOR_QUALIDADE,
            "merge_output_format": "mp4",
            "postprocessors": [POS_PROCESSADOR_MP4.copy()],
            "outtmpl": str(pasta_destino / "%(title)s.%(ext)s"),
        })
    elif formato == "mp4_android_vr":
        opcoes.update({
            "format": FORMATO_MELHOR_QUALIDADE,
            "merge_output_format": "mp4",
            "postprocessors": [POS_PROCESSADOR_MP4.copy()],
            "outtmpl": str(pasta_destino / "%(title)s.%(ext)s"),
            "extractor_args": {"youtube": {"player_client": ["android_vr"]}},
        })
    elif formato == "mp4_compat":
        opcoes.update({
            "format": "best[ext=mp4]/best",
            "merge_output_format": "mp4",
            "postprocessors": [POS_PROCESSADOR_MP4.copy()],
            "outtmpl": str(pasta_destino / "%(title)s.%(ext)s"),
        })
    elif formato == "webm":
        opcoes.update({
            "format": "bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best",
            "merge_output_format": "webm",
            "outtmpl": str(pasta_destino / "%(title)s.%(ext)s"),
        })
    elif formato == "mkv":
        opcoes.update({
            "format": FORMATO_MELHOR_QUALIDADE,
            "merge_output_format": "mkv",
            "postprocessors": [POS_PROCESSADOR_MKV.copy()],
            "outtmpl": str(pasta_destino / "%(title)s.%(ext)s"),
        })
    elif formato == "gif":
        inicio_gif, fim_gif = validar_intervalo_gif(inicio_gif, fim_gif)
        if download_range_func is None:
            raise RuntimeError("O yt-dlp instalado não oferece suporte a recortes por tempo.")
        opcoes.update({
            "format": "bestvideo[height<=720]/bestvideo/best",
            "download_ranges": download_range_func([], [(inicio_gif, fim_gif)]),
            "outtmpl": str(pasta_destino / "%(title)s.%(ext)s"),
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
    return opcoes


class LineEditComPlaceholder(QLineEdit):
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setFixedHeight(ALTURA_CONTROLE - 2)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFont(QFont("Segoe UI", 11))
        self.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {COR_TEXTO};
                padding: 0;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                background: transparent;
            }}
        """)
class BotaoEstiloso(QPushButton):
    def __init__(self, texto, primario=True, parent=None):
        super().__init__(texto, parent)
        self._primario = primario
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(ALTURA_CONTROLE)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        self._setup_style()

    def _setup_style(self):
        if self._primario:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {COR_VERMELHO}, stop:1 {COR_VERMELHO_ESCURO});
                    color: white;
                    border: none;
                    border-radius: {RAIO_BOTAO}px;
                    padding: 12px 24px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {COR_VERMELHO_GLOW}, stop:1 {COR_VERMELHO});
                }}
                QPushButton:pressed {{
                    background: {COR_VERMELHO_ESCURO};
                }}
                QPushButton:disabled {{
                    background: #3a3f4a;
                    color: #6a6f7a;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {COR_CARD};
                    color: {COR_TEXTO};
                    border: 1px solid {COR_BORDA};
                    border-radius: {RAIO_BOTAO}px;
                    padding: 12px 24px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background: {COR_CARD_HOVER};
                    border-color: {COR_VERMELHO};
                }}
                QPushButton:pressed {{
                    background: #252930;
                }}
                QPushButton:disabled {{
                    background: #1a1d23;
                    color: #4a4f5a;
                    border-color: #2d3139;
                }}
            """)


class CardWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(f"""
            QFrame#card {{
                background: {COR_CARD};
                border: 1px solid {COR_BORDA};
                border-radius: {RAIO_CARD}px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)


class CampoContainer(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("campoContainer")
        self.setFixedHeight(ALTURA_CONTROLE)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setProperty("focado", False)
        self.setStyleSheet(f"""
            QFrame#campoContainer {{
                background: {COR_FUNDO};
                border: 1px solid {COR_BORDA};
                border-radius: {RAIO_INPUT}px;
            }}
            QFrame#campoContainer:hover,
            QFrame#campoContainer[focado="true"] {{
                border-color: {COR_VERMELHO};
            }}
            QFrame#campoContainer[focado="true"] {{
                border-width: 2px;
            }}
        """)

    def acompanhar_foco(self, widget):
        widget.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.FocusIn, QEvent.Type.FocusOut):
            self.setProperty("focado", event.type() == QEvent.Type.FocusIn)
            self.style().unpolish(self)
            self.style().polish(self)
            self.update()
        return super().eventFilter(watched, event)


class LinhaPastaResponsiva(QFrame):
    def __init__(self, botao, campo, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self._botao = botao
        self._campo = campo
        self._vertical = None

        self._layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(12)
        self._layout.addWidget(self._botao)
        self._layout.addWidget(self._campo, 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        vertical = event.size().width() < LARGURA_LIMITE_PASTA
        if vertical == self._vertical:
            return

        self._vertical = vertical
        direcao = (
            QBoxLayout.Direction.TopToBottom
            if vertical
            else QBoxLayout.Direction.LeftToRight
        )
        self._layout.setDirection(direcao)
        self._botao.setMaximumWidth(16777215 if vertical else 220)
        self._layout.setStretch(0, 0)
        self._layout.setStretch(1, 1)
        self.setFixedHeight(
            ALTURA_CONTROLE * 2 + self._layout.spacing()
            if vertical
            else ALTURA_CONTROLE
        )
        self._layout.invalidate()
        self.updateGeometry()


class ComboBoxEstiloso(QComboBox):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.addItems(items)
        self.setFixedHeight(ALTURA_CONTROLE - 2)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFont(QFont("Segoe UI", 11))
        self.setStyleSheet(f"""
            QComboBox {{
                background: transparent;
                color: {COR_TEXTO};
                border: none;
                padding: 0 36px 0 0;
                selection-background-color: {COR_VERMELHO};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 36px;
                subcontrol-origin: padding;
                subcontrol-position: top right;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
                width: 0;
                height: 0;
            }}
            QComboBox QAbstractItemView {{
                background: {COR_CARD};
                color: {COR_TEXTO};
                border: 1px solid {COR_BORDA};
                border-radius: 8px;
                selection-background-color: {COR_VERMELHO};
                padding: 4px;
            }}
        """)
        # Seta personalizada via paintEvent
        self._seta_cor = QColor(COR_TEXTO_SUAVE)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Desenha seta no drop-down
        rect = self.rect()
        seta_x = rect.right() - 24
        seta_y = rect.center().y()

        painter.setPen(QPen(self._seta_cor, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(QBrush(self._seta_cor))

        # Triângulo para baixo
        from PySide6.QtGui import QPolygon
        points = QPolygon([
            QPoint(seta_x - 5, seta_y - 2),
            QPoint(seta_x + 5, seta_y - 2),
            QPoint(seta_x, seta_y + 4),
        ])
        painter.drawPolygon(points)

    def enterEvent(self, event):
        self._seta_cor = QColor(COR_VERMELHO)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._seta_cor = QColor(COR_TEXTO_SUAVE)
        self.update()
        super().leaveEvent(event)


class ProgressBarEstilosa(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(24)
        self.setTextVisible(False)
        self.setRange(0, 100)
        self.setValue(0)
        self.setStyleSheet(f"""
            QProgressBar {{
                background: {COR_FUNDO};
                border: 2px solid {COR_BORDA};
                border-radius: {RAIO_PROGRESSO}px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COR_VERMELHO}, stop:1 {COR_VERMELHO_GLOW});
                border-radius: {RAIO_PROGRESSO - 2}px;
                margin: 2px;
            }}
        """)


class DownloadWorker(QObject):
    progresso_atualizado = Signal(str, int, int)
    download_concluido = Signal()
    download_erro = Signal(str)
    status_atualizado = Signal(str)

    def __init__(
        self,
        url,
        caminho,
        formato,
        playlist,
        inicio_gif=None,
        fim_gif=None,
    ):
        super().__init__()
        self.url = url
        self.caminho = caminho
        self.formato = formato
        self.playlist = playlist
        self.inicio_gif = inicio_gif
        self.fim_gif = fim_gif
        self._cancelado = False

    def cancelar(self):
        self._cancelado = True

    def run(self):
        total_videos = 0
        self.status_atualizado.emit("Iniciando download...")
        self.progresso_atualizado.emit("Iniciando download...", 0, 100)

        try:
            verificar_dependencias()
            if self.playlist:
                self.status_atualizado.emit("Lendo playlist...")
                self.progresso_atualizado.emit("Lendo playlist...", 0, 100)
                total_videos = contar_videos_playlist(self.url)

            def hook(dados):
                if self._cancelado:
                    raise Exception("Download cancelado pelo usuário")

                status = dados.get("status")

                if self.playlist:
                    indice = dados.get("info_dict", {}).get("playlist_index")
                    if total_videos and indice:
                        valor = min(indice, total_videos)
                        texto = f"Baixando vídeo {valor} de {total_videos}..."
                        self.progresso_atualizado.emit(texto, valor, total_videos)
                    elif status in {"downloading", "finished"}:
                        self.status_atualizado.emit("Baixando playlist...")
                    return

                if status == "downloading":
                    total = dados.get("total_bytes") or dados.get("total_bytes_estimate") or 0
                    baixado = dados.get("downloaded_bytes") or 0
                    if total > 0:
                        porcentagem = baixado / total * 100
                        texto = f"Baixando... {porcentagem:.1f}%"
                        self.progresso_atualizado.emit(texto, int(porcentagem), 100)
                    else:
                        self.status_atualizado.emit("Baixando...")
                elif status == "finished":
                    self.progresso_atualizado.emit("Finalizando e convertendo...", 100, 100)

            def hook_posprocessamento(dados):
                status = dados.get("status")
                if status == "started":
                    mensagem = (
                        "Reduzindo e convertendo o trecho para GIF..."
                        if self.formato == "gif"
                        else "Finalizando e convertendo..."
                    )
                    self.status_atualizado.emit(mensagem)
                    self.progresso_atualizado.emit(mensagem, 0, 0)
                elif status == "finished":
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
                )
                if self.formato == "gif":
                    mensagem = "Baixando e recortando o trecho do vídeo..."
                    self.status_atualizado.emit(mensagem)
                    self.progresso_atualizado.emit(mensagem, 0, 0)
                with YoutubeDL(opcoes) as ydl:
                    ydl.download([self.url])
            except Exception as erro_download:
                if self.formato != "mp4" or not erro_http_403(erro_download):
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
            self.download_erro.emit(limpar_mensagem_erro(erro))


class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Downloader")
        self.setFixedSize(980, 760)

        self.pasta_selecionada = ""
        self.worker_thread = None
        self.worker = None

        self._setup_icon()
        self._setup_ui()
        self._centralizar_janela()
        self._aplicar_estilo_global()

    def _setup_icon(self):
        icone_path = caminho_icone()
        if icone_path.exists():
            self.setWindowIcon(QIcon(str(icone_path)))

    def _aplicar_estilo_global(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {COR_FUNDO};
            }}
            QLabel {{
                color: {COR_TEXTO};
                background: transparent;
            }}
            QMessageBox {{
                background: {COR_CARD};
                color: {COR_TEXTO};
            }}
            QMessageBox QPushButton {{
                background: {COR_VERMELHO};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                min-width: 80px;
                font-weight: 600;
            }}
            QMessageBox QPushButton:hover {{
                background: {COR_VERMELHO_GLOW};
            }}
            QFileDialog {{
                background: {COR_FUNDO};
                color: {COR_TEXTO};
            }}
            QScrollBar:vertical {{
                background: {COR_FUNDO};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {COR_BORDA};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {COR_VERMELHO};
            }}
            QToolTip {{
                background: {COR_CARD};
                color: {COR_TEXTO};
                border: 1px solid {COR_BORDA};
                border-radius: 6px;
                padding: 8px;
            }}
        """)

    def _centralizar_janela(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        conteudo = QWidget()
        conteudo.setStyleSheet(f"background: {COR_FUNDO};")
        self._layout_conteudo = QVBoxLayout(conteudo)
        self._layout_conteudo.setContentsMargins(24, 16, 24, 16)
        self._layout_conteudo.setSpacing(12)
        self._layout_conteudo.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        self._header = self._criar_header()
        self._card = self._criar_card_principal()
        self._rodape = self._criar_rodape()
        self._layout_conteudo.addWidget(self._header)
        self._layout_conteudo.addWidget(self._card)
        self._layout_conteudo.addWidget(self._rodape)
        self._layout_conteudo.addStretch(1)

        self.scroll_area.setWidget(conteudo)
        main_layout.addWidget(self.scroll_area)

    def _criar_header(self):
        header = QFrame()
        header.setStyleSheet("background: transparent;")
        header.setFixedHeight(64)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        self._titulo = QLabel("YouTube Downloader")
        self._titulo.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        self._titulo.setStyleSheet(f"color: {COR_TEXTO};")
        layout.addWidget(self._titulo)

        layout.addStretch()

        versao = QLabel("v3")
        versao.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        versao.setStyleSheet(f"""
            color: {COR_VERMELHO};
            padding: 4px 12px;
            background: {COR_VERMELHO_CLARO};
            border-radius: 10px;
        """)
        versao.setAlignment(Qt.AlignmentFlag.AlignCenter)
        versao.setFixedHeight(28)
        layout.addWidget(versao, 0, Qt.AlignmentFlag.AlignVCenter)

        return header

    def _criar_card_principal(self):
        card = CardWidget()
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self._card_layout = QVBoxLayout(card)
        self._card_layout.setContentsMargins(36, 20, 36, 20)
        self._card_layout.setSpacing(16)

        linha_acento = QFrame()
        linha_acento.setFixedHeight(3)
        linha_acento.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.1 {COR_VERMELHO}, stop:0.9 {COR_VERMELHO}, stop:1 transparent);
            border-radius: 1.5px;
        """)
        self._card_layout.addWidget(linha_acento)

        self._card_layout.addWidget(self._criar_formulario())
        self._card_layout.addWidget(self._criar_progresso_area())

        return card

    def _criar_grupo_campo(self, titulo, controle):
        grupo = QFrame()
        grupo.setStyleSheet("background: transparent;")
        grupo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        layout = QVBoxLayout(grupo)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QLabel(titulo)
        label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        label.setStyleSheet(f"color: {COR_TEXTO};")
        layout.addWidget(label)
        layout.addWidget(controle)
        return grupo

    def _criar_input_estilizado(self, placeholder, icone=""):
        campo = LineEditComPlaceholder(placeholder)
        container = CampoContainer()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        if icone:
            label_icone = QLabel(icone)
            label_icone.setFont(QFont("Segoe UI", 16))
            label_icone.setStyleSheet(
                f"color: {COR_TEXTO_SUAVE}; background: transparent;"
            )
            label_icone.setFixedWidth(28)
            label_icone.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label_icone)

        layout.addWidget(campo, 1)
        container.acompanhar_foco(campo)
        return campo, container

    def _criar_formulario(self):
        form = QFrame()
        form.setStyleSheet("background: transparent;")
        form.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        layout = QVBoxLayout(form)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self.input_url, url_container = self._criar_input_estilizado(
            "Cole aqui o link do vídeo do YouTube...",
            "🔗",
        )
        layout.addWidget(self._criar_grupo_campo("Link do Vídeo", url_container))

        self.btn_pasta = BotaoEstiloso("Selecionar pasta", primario=False)
        self.btn_pasta.clicked.connect(self._escolher_pasta)

        self.label_pasta = QLabel("Nenhuma pasta selecionada")
        self.label_pasta.setFont(QFont("Segoe UI", 11))
        self.label_pasta.setStyleSheet(f"color: {COR_TEXTO_SUAVE};")
        self.label_pasta.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.label_pasta.setMinimumWidth(0)
        self.label_pasta.setWordWrap(False)
        self.label_pasta.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.label_pasta.setToolTip("Nenhuma pasta selecionada")

        pasta_container = CampoContainer()
        pasta_container_layout = QHBoxLayout(pasta_container)
        pasta_container_layout.setContentsMargins(16, 0, 16, 0)
        pasta_container_layout.setSpacing(12)
        pasta_container_layout.addWidget(self.label_pasta, 1)

        icon_pasta = QLabel("📁")
        icon_pasta.setFont(QFont("Segoe UI", 16))
        icon_pasta.setStyleSheet(f"color: {COR_TEXTO_SUAVE};")
        icon_pasta.setFixedWidth(28)
        icon_pasta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pasta_container_layout.addWidget(icon_pasta)

        self._linha_pasta = LinhaPastaResponsiva(self.btn_pasta, pasta_container)
        layout.addWidget(self._criar_grupo_campo("Pasta de Destino", self._linha_pasta))

        self.combo_formato = ComboBoxEstiloso(list(FORMATOS_SAIDA.keys()))
        formato_container = CampoContainer()
        formato_container_layout = QHBoxLayout(formato_container)
        formato_container_layout.setContentsMargins(16, 0, 16, 0)
        formato_container_layout.setSpacing(12)

        icon_formato = QLabel("📄")
        icon_formato.setFont(QFont("Segoe UI", 16))
        icon_formato.setStyleSheet(f"color: {COR_TEXTO_SUAVE};")
        icon_formato.setFixedWidth(28)
        icon_formato.setAlignment(Qt.AlignmentFlag.AlignCenter)
        formato_container_layout.addWidget(icon_formato)
        formato_container_layout.addWidget(self.combo_formato, 1)
        formato_container.acompanhar_foco(self.combo_formato)

        layout.addWidget(self._criar_grupo_campo("Formato de Saída", formato_container))

        self.input_gif_inicio, gif_inicio_container = self._criar_input_estilizado(
            "Ex.: 00:10",
            "⏱",
        )
        self.input_gif_fim, gif_fim_container = self._criar_input_estilizado(
            "Ex.: 00:20",
            "⏱",
        )
        self.input_gif_inicio.setMaxLength(12)
        self.input_gif_fim.setMaxLength(12)
        dica_tempo_gif = (
            "Aceita segundos, mm:ss ou hh:mm:ss. "
            f"O trecho pode ter no máximo {DURACAO_MAXIMA_GIF} segundos."
        )
        self.input_gif_inicio.setToolTip(dica_tempo_gif)
        self.input_gif_fim.setToolTip(dica_tempo_gif)

        self._opcoes_gif = QFrame()
        self._opcoes_gif.setStyleSheet("background: transparent;")
        self._opcoes_gif.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum,
        )
        opcoes_gif_layout = QHBoxLayout(self._opcoes_gif)
        opcoes_gif_layout.setContentsMargins(0, 0, 0, 0)
        opcoes_gif_layout.setSpacing(12)
        opcoes_gif_layout.addWidget(
            self._criar_grupo_campo("Tempo inicial do GIF", gif_inicio_container),
            1,
        )
        opcoes_gif_layout.addWidget(
            self._criar_grupo_campo("Tempo final do GIF", gif_fim_container),
            1,
        )
        self._opcoes_gif.setVisible(False)
        layout.addWidget(self._opcoes_gif)

        self.btn_baixar = BotaoEstiloso("Baixar Vídeo", primario=True)
        self.btn_baixar.clicked.connect(self._iniciar_download)
        layout.addWidget(self.btn_baixar)

        self.combo_formato.currentTextChanged.connect(self._atualizar_opcoes_formato)
        self._atualizar_opcoes_formato()

        return form

    def _formato_selecionado(self):
        formato_key = self.combo_formato.currentText()
        return FORMATOS_SAIDA.get(formato_key, formato_key)

    def _texto_botao_formato(self, formato):
        if formato == "gif":
            return "Gerar GIF"
        if formato in {"mp3", "wav"}:
            return "Baixar Áudio"
        return "Baixar Vídeo"

    def _mensagens_resultado(self, formato):
        if formato == "gif":
            return "GIF gerado com sucesso!", "Falha ao gerar o GIF"
        if formato in {"mp3", "wav"}:
            return "Áudio concluído com sucesso!", "Falha ao gerar o áudio"
        return "Download concluído!", "Falha ao baixar o vídeo"

    def _atualizar_opcoes_formato(self):
        formato = self._formato_selecionado()
        self._opcoes_gif.setVisible(formato == "gif")
        if self.btn_baixar.isEnabled():
            self.btn_baixar.setText(self._texto_botao_formato(formato))
        if hasattr(self, "_card"):
            self._card.updateGeometry()
        if self.scroll_area.widget() is not None:
            self.scroll_area.widget().updateGeometry()

    def _criar_progresso_area(self):
        area = QFrame()
        area.setStyleSheet("background: transparent;")
        area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        layout = QVBoxLayout(area)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(10)

        titulo_progresso = QLabel("Progresso")
        titulo_progresso.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        titulo_progresso.setStyleSheet(f"color: {COR_TEXTO};")
        titulo_progresso.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo_progresso)

        self.progress_bar = ProgressBarEstilosa()
        layout.addWidget(self.progress_bar)

        self.label_status = QLabel("Aguardando...")
        self.label_status.setFont(QFont("Segoe UI", 10))
        self.label_status.setStyleSheet(f"color: {COR_TEXTO_SUAVE};")
        self.label_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_status.setWordWrap(True)
        layout.addWidget(self.label_status)

        return area

    def _criar_rodape(self):
        rodape = QFrame()
        rodape.setStyleSheet("background: transparent;")
        rodape.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        layout = QVBoxLayout(rodape)
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(8)

        linha = QFrame()
        linha.setFixedHeight(1)
        linha.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        linha.setStyleSheet(f"background: {COR_BORDA};")
        layout.addWidget(linha)

        estrela = QLabel("★")
        estrela.setFont(QFont("Segoe UI", 18))
        estrela.setStyleSheet(f"color: {COR_VERMELHO};")
        estrela.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(estrela, 0, Qt.AlignmentFlag.AlignHCenter)

        direitos = QLabel("Licença GPLv3\nDesenvolvido principalmente com Inteligência Artificial")
        direitos.setFont(QFont("Segoe UI", 9))
        direitos.setStyleSheet(f"color: {COR_TEXTO_SUAVE};")
        direitos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        direitos.setWordWrap(True)
        layout.addWidget(direitos, 0, Qt.AlignmentFlag.AlignHCenter)

        versao = QLabel("V 3")
        versao.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        versao.setStyleSheet(f"color: {COR_VERMELHO};")
        versao.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(versao, 0, Qt.AlignmentFlag.AlignHCenter)

        return rodape

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not hasattr(self, "_layout_conteudo"):
            return

        compacto = event.size().width() < 820
        margem_externa = 12 if compacto else 24
        margem_vertical = 12 if compacto else 16
        margem_card_horizontal = 16 if compacto else 36
        margem_card_vertical = 16 if compacto else 20

        self._layout_conteudo.setContentsMargins(
            margem_externa,
            margem_vertical,
            margem_externa,
            margem_vertical,
        )
        self._card_layout.setContentsMargins(
            margem_card_horizontal,
            margem_card_vertical,
            margem_card_horizontal,
            margem_card_vertical,
        )
        self._header.setFixedHeight(58 if compacto else 64)
        self._titulo.setFont(QFont("Segoe UI", 22 if compacto else 28, QFont.Weight.Bold))

    def _escolher_pasta(self):
        pasta = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Destino")
        if pasta:
            self.pasta_selecionada = pasta
            self.label_pasta.setText(pasta)
            self.label_pasta.setStyleSheet(f"color: {COR_TEXTO};")
            self.label_pasta.setToolTip(pasta)

    def _iniciar_download(self):
        url = normalizar_url(self.input_url.text())
        caminho = self.pasta_selecionada
        formato = self._formato_selecionado()
        inicio_gif = None
        fim_gif = None

        if not url or not url_do_youtube(url):
            QMessageBox.critical(self, "Erro", "URL inválida! Insira um link válido do YouTube.")
            return

        if not caminho:
            QMessageBox.critical(self, "Erro", "Nenhuma pasta selecionada!")
            return

        if formato == "gif":
            try:
                inicio_gif, fim_gif = validar_intervalo_gif(
                    self.input_gif_inicio.text(),
                    self.input_gif_fim.text(),
                )
            except ValueError as erro:
                QMessageBox.critical(self, "Intervalo do GIF inválido", str(erro))
                return

        playlist = False
        url_download = url

        if url_tem_playlist(url):
            resposta = QMessageBox.question(
                self, "Playlist detectada",
                "O link contém uma playlist. Deseja baixar todos os vídeos?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            playlist = resposta == QMessageBox.StandardButton.Yes
            if not playlist:
                url_download = remover_playlist_da_url(url)

        self.btn_baixar.setEnabled(False)
        self.btn_baixar.setText("Processando...")
        self.combo_formato.setEnabled(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.label_status.setText("Iniciando...")

        self.worker = DownloadWorker(
            url_download,
            caminho,
            formato,
            playlist,
            inicio_gif,
            fim_gif,
        )
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)

        self.worker.progresso_atualizado.connect(self._atualizar_progresso)
        self.worker.status_atualizado.connect(self._atualizar_status)
        self.worker.download_concluido.connect(self._download_sucesso)
        self.worker.download_erro.connect(self._download_erro)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.download_concluido.connect(self.worker_thread.quit)
        self.worker.download_erro.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self.worker.deleteLater)

        self.worker_thread.start()

    def _atualizar_progresso(self, texto, valor, maximo):
        self.progress_bar.setRange(0, maximo)
        self.progress_bar.setValue(valor)

    def _atualizar_status(self, texto):
        self.label_status.setText(texto)

    def _download_sucesso(self):
        formato = self.worker.formato if self.worker else self._formato_selecionado()
        mensagem_sucesso, _ = self._mensagens_resultado(formato)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.label_status.setText(mensagem_sucesso)
        self.btn_baixar.setEnabled(True)
        self.combo_formato.setEnabled(True)
        self._atualizar_opcoes_formato()
        QMessageBox.information(self, "Pronto!", mensagem_sucesso)

    def _download_erro(self, erro):
        formato = self.worker.formato if self.worker else self._formato_selecionado()
        _, mensagem_erro = self._mensagens_resultado(formato)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.label_status.setText(f"{mensagem_erro}.")
        self.btn_baixar.setEnabled(True)
        self.combo_formato.setEnabled(True)
        self._atualizar_opcoes_formato()
        QMessageBox.critical(self, "Erro", f"{mensagem_erro}:\n{erro}")

    def closeEvent(self, event):
        if self.worker_thread and self.worker_thread.isRunning():
            if self.worker:
                self.worker.cancelar()
            self.worker_thread.quit()
            self.worker_thread.wait(3000)
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("YouTube Downloader")
    app.setApplicationVersion("3")
    app.setOrganizationName("UIfor_yt-dlp")

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    janela = JanelaPrincipal()
    janela.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
