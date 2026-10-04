"""Cancelable Qt metadata child, using local IPC (also in windowed EXEs)."""
import json
import sys
import uuid
from PySide6.QtCore import QObject, QCoreApplication, QProcess, QTimer, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from media_sources import classify_url, friendly_error, lookup_metadata


class MetadataLookup(QObject):
    finished = Signal(dict)
    failed = Signal(str)
    MAX_BYTES = 1024 * 1024

    def __init__(self, entrypoint, url, timeout=12000, parent=None):
        super().__init__(parent)
        self.done = False
        self.data = bytearray()
        self.server = QLocalServer(self)
        self.name = "uifor-metadata-" + uuid.uuid4().hex
        self.process = QProcess(self)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(lambda: self.complete(error="A consulta demorou demais. Tente baixar novamente."))
        self.server.newConnection.connect(self.connected)
        self.process.errorOccurred.connect(lambda _: self.complete(error="Não foi possível iniciar a consulta de mídia."))
        self.process.finished.connect(lambda *_: QTimer.singleShot(100, self.process_ended))
        self.url = url
        self.entrypoint = str(entrypoint)
        self.timeout = timeout

    def start(self):
        if not self.server.listen(self.name):
            self.complete(error="Não foi possível iniciar a consulta local.")
            return
        args = ["--media-info", self.name, self.url]
        if not getattr(sys, "frozen", False):
            args.insert(0, self.entrypoint)
        self.process.start(sys.executable, args)
        self.timer.start(self.timeout)

    def connected(self):
        socket = self.server.nextPendingConnection()
        socket.readyRead.connect(lambda: self.read(socket))
        socket.disconnected.connect(socket.deleteLater)
        self.read(socket)

    def read(self, socket):
        self.data.extend(bytes(socket.readAll()))
        if len(self.data) > self.MAX_BYTES:
            self.complete(error="A resposta de metadados excedeu o limite.")
        elif b"\n" in self.data:
            try:
                answer = json.loads(self.data.split(b"\n", 1)[0])
                self.complete(result=answer.get("result"), error=answer.get("error"))
            except (ValueError, AttributeError):
                self.complete(error="Resposta de metadados inválida.")

    def process_ended(self):
        if not self.done:
            self.complete(error="A consulta terminou sem informações da mídia.")

    def cancel(self):
        if self.done:
            return
        self.done = True
        self.cleanup()

    def cleanup(self):
        self.timer.stop()
        self.server.close()
        QLocalServer.removeServer(self.name)
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
            self.process.waitForFinished(1000)

    def complete(self, result=None, error=None):
        if self.done:
            return
        self.done = True
        self.cleanup()
        if isinstance(result, dict):
            self.finished.emit(result)
        else:
            self.failed.emit(error or "Nenhum vídeo disponível nesse post.")


def run_helper(name, url, options):
    app = QCoreApplication.instance() or QCoreApplication([])
    socket = QLocalSocket()
    socket.connectToServer(name)
    if not socket.waitForConnected(3000):
        return 1
    try:
        answer = {"result": lookup_metadata(url, options)}
    except Exception as error:
        source = classify_url(url)
        answer = {"error": friendly_error(error, source["name"] if source else "essa fonte")}
    payload = json.dumps(answer, ensure_ascii=False).encode("utf-8") + b"\n"
    socket.write(payload)
    socket.waitForBytesWritten(3000)
    socket.disconnectFromServer()
    return 0
