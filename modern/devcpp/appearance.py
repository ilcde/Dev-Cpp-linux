from __future__ import annotations
import asyncio
import threading
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Qt, QUrl
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QWidget
from PySide6.QtMultimedia import QMediaPlayer, QVideoSink


class Background(QWidget):
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self.color = QColor("#202124")
        self.opacity = 0.22
        self.image = QPixmap()
        self.player = QMediaPlayer(self)
        self.sink = QVideoSink(self)
        self.player.setVideoSink(self.sink)
        self.player.setLoops(QMediaPlayer.Loops.Infinite)
        self.sink.videoFrameChanged.connect(self.frame)
        self.player.errorOccurred.connect(lambda *_: self.error.emit(self.player.errorString()))

    def frame(self, frame):
        if frame.isValid():
            self.image = QPixmap.fromImage(frame.toImage())
            self.update()

    def configure(self, path, color, opacity):
        self.player.stop()
        self.player.setSource(QUrl())
        self.color = QColor(color)
        self.opacity = opacity
        self.image = QPixmap()
        if path:
            if Path(path).suffix.lower() in (".mp4", ".webm", ".mkv", ".mov"):
                self.player.setSource(QUrl.fromLocalFile(path))
                self.player.play()
            else:
                self.image = QPixmap(path)
                if self.image.isNull():
                    self.error.emit("Không đọc được ảnh / Cannot load image: " + path)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.color)
        if not self.image.isNull():
            painter.setOpacity(self.opacity)
            image = self.image.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap((self.width() - image.width()) // 2, (self.height() - image.height()) // 2, image)


class Presence(QObject):
    status = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stop_event = threading.Event()
        self.worker = None

    def start(self, client_id):
        self.stop()
        if not client_id:
            return
        self.stop_event = threading.Event()
        self.worker = threading.Thread(target=self.run, args=(client_id, self.stop_event), daemon=True)
        self.worker.start()

    def run(self, client_id, stop):
        from pypresence import Presence as DiscordPresence
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        rpc = None
        try:
            rpc = DiscordPresence(client_id, loop=loop)
            rpc.connect()
            if stop.is_set():
                return
            rpc.update(details="C / C++", state="Dev-C++ Modern")
            self.status.emit("Discord RPC: connected")
            stop.wait()
        except Exception as exc:
            self.status.emit("Discord RPC: " + str(exc))
        finally:
            if rpc:
                try:
                    rpc.close()
                except Exception:
                    pass
            if not loop.is_closed():
                loop.close()

    def stop(self):
        self.stop_event.set()
        if self.worker:
            self.worker.join(timeout=1)


STYLE = """
QMainWindow, QDialog { background: #202124; color: #d7d9dd; }
QWidget { color: #d7d9dd; font-family: 'Segoe UI', 'Noto Sans', sans-serif; font-size: 13px; }
QMenuBar, QMenu { background: #292a2e; padding: 2px; border: 0; }
QToolBar { background: #292a2e; padding: 4px 8px; border-bottom: 1px solid #17181a; spacing: 3px; }
QToolBar::separator { background: #43454a; width: 1px; margin: 5px 8px; }
QMenu::item:selected, QMenuBar::item:selected { background: #41454b; }
QToolButton { background: transparent; border: 0; border-radius: 3px; padding: 5px; }
QPushButton { background: #34363b; border: 1px solid #494c53; border-radius: 3px; padding: 5px 10px; }
QToolButton:hover, QPushButton:hover { background: #43464d; }
QToolButton:disabled, QPushButton:disabled { color: #64748b; }
QPlainTextEdit, QTextEdit, QTreeView, QListWidget, QTreeWidget { background: rgba(32,33,36,215); border: 0; selection-background-color: #3c5055; }
QTreeView { padding: 8px 4px; }
QTreeView::item { height: 25px; }
QLineEdit, QComboBox, QSpinBox { background: #25262a; border: 1px solid #484b52; border-radius: 3px; padding: 5px; }
QTabWidget::pane { border: 0; border-top: 1px solid #37393e; background: transparent; }
QTabBar::tab { background: #292a2e; padding: 8px 12px; color: #969ca6; border-right: 1px solid #202124; }
QTabBar::tab:selected { background: #202124; color: #eef0f3; border-top: 2px solid #83bdb2; padding-top: 6px; }
QHeaderView::section { background: #292a2e; color: #b1b7c0; border: 0; padding: 5px; }
QSplitter::handle { background: #161719; width: 1px; height: 1px; }
QStatusBar { background: #292a2e; color: #a9b0ba; border-top: 1px solid #37393e; }
QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: #4b4d53; min-height: 25px; border-radius: 3px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QLabel#muted { color: #9da4ae; padding: 0 8px; }
QPlainTextEdit#codeEditor, QTextEdit#terminal { font-family: 'Consolas', 'DejaVu Sans Mono', monospace; font-size: 15px; }
"""
