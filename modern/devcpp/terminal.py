"""Native ANSI terminal backed by ConPTY on Windows and a PTY on Linux."""
from __future__ import annotations
import html
import os
import shlex
import subprocess
import threading
from pathlib import Path
import pyte
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import QApplication, QTextEdit


class Terminal(QTextEdit):
    received = Signal(str)
    ended = Signal(str)

    def __init__(self, root: Path, parent=None, command=None):
        super().__init__(parent)
        self.setObjectName("terminal")
        self.setReadOnly(True)
        self.setFont(QFont("Cascadia Mono" if os.name == "nt" else "monospace", 11))
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.screen = pyte.HistoryScreen(100, 24, history=2000)
        self.stream = pyte.Stream(self.screen)
        self.received.connect(self.feed)
        self.ended.connect(self.on_end)
        self.pty = None
        self.closing = False
        self.dirty = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.render)
        self.timer.start(33)
        env = dict(os.environ, TERM="xterm-256color", COLORTERM="truecolor")
        try:
            if os.name == "nt":
                from winpty import PtyProcess
                self.pty = PtyProcess.spawn(subprocess.list2cmdline(command) if command else "powershell.exe -NoLogo -NoProfile", cwd=str(root), env=env, dimensions=(24, 100))
            else:
                from ptyprocess import PtyProcessUnicode
                self.pty = PtyProcessUnicode.spawn(command or [os.environ.get("SHELL", "/bin/bash"), "-i"], cwd=str(root), env=env, dimensions=(24, 100))
            self.reader = threading.Thread(target=self.read_loop, daemon=True)
            self.reader.start()
        except Exception as exc:
            self.on_end(str(exc))

    def read_loop(self):
        try:
            while not self.closing:
                text = self.pty.read(8192)
                if text:
                    self.received.emit(text)
                elif not self.pty.isalive():
                    break
        except (EOFError, OSError) as exc:
            if not self.closing:
                self.ended.emit(str(exc))

    def on_end(self, message):
        self.feed("\r\n[Terminal đã kết thúc / exited] " + message + "\r\n")

    def feed(self, text):
        self.stream.feed(text)
        self.dirty = True

    def write(self, text):
        if self.pty and not self.closing:
            try:
                self.pty.write(text)
            except (EOFError, OSError) as exc:
                self.on_end(str(exc))

    def run_program(self, executable: Path, arguments: list[str]):
        if os.name == "nt":
            quote = lambda value: "'" + str(value).replace("'", "''") + "'"
            command = "& " + " ".join(quote(v) for v in [str(executable), *arguments])
        else:
            command = shlex.join([str(executable), *arguments])
        self.write(command + "\r")

    def render(self):
        if not self.dirty or self.textCursor().hasSelection():
            return
        self.dirty = False
        colors = {"black": "#111827", "red": "#fb7185", "green": "#6ee7b7", "brown": "#fbbf24",
                  "blue": "#60a5fa", "magenta": "#c084fc", "cyan": "#67e8f9", "white": "#e2e8f0", "default": "#dce5f3"}
        rows = []
        for y in range(self.screen.lines):
            row = []
            for x in range(self.screen.columns):
                char = self.screen.buffer[y][x]
                fg = colors.get(char.fg, "#" + char.fg)
                bg = "transparent" if char.bg == "default" else colors.get(char.bg, "#" + char.bg)
                if char.reverse:
                    fg, bg = bg if bg != "transparent" else "#111827", fg
                if x == self.screen.cursor.x and y == self.screen.cursor.y and self.hasFocus():
                    bg = "#425b76"
                style = f"color:{fg};background-color:{bg};" + ("font-weight:bold;" if char.bold else "")
                row.append(f'<span style="{style}">{html.escape(char.data)}</span>')
            rows.append("".join(row))
        self.setHtml('<pre style="margin:0;">' + "\n".join(rows) + "</pre>")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not hasattr(self, "screen"):
            return
        metrics = self.fontMetrics()
        cols = max(20, (self.viewport().width() - 12) // max(1, metrics.horizontalAdvance("M")))
        rows = max(4, (self.viewport().height() - 12) // metrics.lineSpacing())
        self.screen.resize(rows, cols)
        if self.pty:
            try:
                self.pty.setwinsize(rows, cols)
            except OSError:
                pass
        self.dirty = True

    def keyPressEvent(self, event):
        key, mods = event.key(), event.modifiers()
        control = bool(mods & Qt.KeyboardModifier.ControlModifier)
        shift = bool(mods & Qt.KeyboardModifier.ShiftModifier)
        if control and shift and key == Qt.Key.Key_C:
            self.copy()
            return
        if control and shift and key == Qt.Key.Key_V:
            self.write(QApplication.clipboard().text())
            return
        if shift and key in (Qt.Key.Key_PageUp, Qt.Key.Key_PageDown):
            (self.screen.prev_page if key == Qt.Key.Key_PageUp else self.screen.next_page)()
            self.dirty = True
            return
        sequences = {Qt.Key.Key_Return: "\r", Qt.Key.Key_Enter: "\r", Qt.Key.Key_Backspace: "\x7f",
                     Qt.Key.Key_Tab: "\t", Qt.Key.Key_Escape: "\x1b", Qt.Key.Key_Up: "\x1b[A",
                     Qt.Key.Key_Down: "\x1b[B", Qt.Key.Key_Right: "\x1b[C", Qt.Key.Key_Left: "\x1b[D",
                     Qt.Key.Key_Home: "\x1b[H", Qt.Key.Key_End: "\x1b[F", Qt.Key.Key_Delete: "\x1b[3~"}
        if control and Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
            self.write(chr(key - Qt.Key.Key_A + 1))
        elif key in sequences:
            self.write(sequences[key])
        elif event.text():
            self.write(event.text())

    def inputMethodEvent(self, event):
        if event.commitString():
            self.write(event.commitString())
        event.accept()

    def shutdown(self):
        self.closing = True
        self.timer.stop()
        if self.pty:
            try:
                if os.name == "nt":
                    # Only terminate this terminal's process tree.
                    subprocess.run(["taskkill", "/PID", str(self.pty.pid), "/T", "/F"], capture_output=True, timeout=3,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    import signal
                    os.killpg(self.pty.pid, signal.SIGHUP)
                self.pty.close(force=True)
            except (OSError, EOFError, subprocess.TimeoutExpired):
                pass
        if hasattr(self, "reader"):
            self.reader.join(timeout=1)
