"""Render the actual Qt window offscreen for visual QA; no terminal or RPC."""
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from pathlib import Path
import tempfile
from PySide6.QtCore import QSettings, QTimer
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication
from devcpp.app import Window
from devcpp.appearance import STYLE

app = QApplication([])
if os.name == "nt":
    for name in ["segoeui.ttf", "seguisb.ttf", "consola.ttf"]:
        QFontDatabase.addApplicationFont(str(Path(os.environ["WINDIR"]) / "Fonts" / name))
app.setStyle("Fusion")
app.setStyleSheet(STYLE)
root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as temp:
    settings = QSettings(str(Path(temp) / "settings.ini"), QSettings.Format.IniFormat)
    win = Window(root / "examples" / "hello", settings)
    win.close_tab(0)
    win.open_file(root / "examples" / "hello" / "main.cpp")
    win.show()

    def capture():
        target = root / "preview.png"
        win.grab().save(str(target))
        print(target)
        win.close()
        app.quit()

    QTimer.singleShot(500, capture)
    app.exec()
