"""Capture real widgets in both languages, including a hostile bright wallpaper."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import sys
import tempfile
import time
from pathlib import Path
from PySide6.QtCore import QSettings
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication
from devcpp.app import Window
from devcpp.appearance import STYLE
from devcpp.dialogs import ProjectDialog, SettingsDialog
from devcpp.terminal import Terminal

app = QApplication([])
app.setStyle("Fusion")
app.setStyleSheet(STYLE)
if os.name == "nt":
    for name in ("segoeui.ttf", "seguisb.ttf", "consola.ttf"):
        QFontDatabase.addApplicationFont(str(Path(os.environ["WINDIR"]) / "Fonts" / name))
modern = Path(__file__).resolve().parents[1]
output = modern / "ci-artifacts" / "ui-audit"
output.mkdir(parents=True, exist_ok=True)

def settle():
    end = time.monotonic() + .25
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(.01)

with tempfile.TemporaryDirectory() as temp:
    for language in ("vi", "en"):
        settings = QSettings(str(Path(temp) / (language + ".ini")), QSettings.Format.IniFormat)
        settings.setValue("language", language)
        settings.setValue("background", "#00a0b0")
        win = Window(modern / "examples/hello", settings)
        win.close_tab(0)
        win.open_file(modern / "examples/hello/main.cpp")
        win.show()
        terminal = Terminal(Path(temp), command=[sys.executable, "-c", "print('Hello from Dev-C++', flush=True)"])
        win.add_terminal(terminal, "Program")
        end = time.monotonic() + 15
        while not terminal.finished and time.monotonic() < end:
            settle()
        for panel, name in enumerate(("build", "terminal", "debug")):
            win.panels.setCurrentIndex(panel)
            settle()
            win.grab().save(str(output / f"{language}-{name}.png"))
        win.sidebar.setCurrentIndex(1)
        win.resize(950, 640)
        settle()
        win.grab().save(str(output / f"{language}-compact-git.png"))
        for dialog, name in ((ProjectDialog(win.project, win.vi, win), "project"),
                             (SettingsDialog(settings, win.vi, win), "settings")):
            dialog.show()
            settle()
            dialog.grab().save(str(output / f"{language}-{name}.png"))
            dialog.reject()
        win.close()
print(output)
