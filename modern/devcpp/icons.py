"""Small original line icons, drawn at runtime for crisp native HiDPI controls."""
from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from pathlib import Path


def application_icon():
    """Keep the original Dev-C++ identity in the native port."""
    return QIcon(str(Path(__file__).parent / "assets" / "devcpp.ico"))

PATHS = {
    "file": '<path d="M6 3h8l4 4v14H6z M14 3v5h4 M9 12h6 M9 16h6"/>',
    "folder": '<path d="M3 6h7l2 2h9v12H3z M3 6V4h7l2 2"/>',
    "save": '<path d="M4 3h14l3 3v15H3V3z M7 3v6h10V3 M7 21v-8h10v8"/>',
    "build": '<path d="m4 3 6 6-3 3-6-6 M10 9l10 10-3 3L7 12 M15 9a5 5 0 0 0 6-6l-3 3-3-3 3-3a5 5 0 0 0-6 6 M9 15l-5 5"/>',
    "run": '<path d="m7 4 13 8-13 8z" fill="{color}" stroke="none"/>',
    "debug": '<rect x="7" y="7" width="10" height="13" rx="5"/><path d="m9 7-2-4 M15 7l2-4 M3 10h4 M17 10h4 M3 15h4 M17 15h4 M5 21l3-3 M19 21l-3-3 M12 9v8"/>',
    "stop": '<rect x="6" y="6" width="12" height="12" rx="1" fill="{color}" stroke="none"/>',
    "terminal": '<path d="m4 6 5 5-5 5 M12 17h8"/>',
    "settings": '<path d="M4 6h16 M4 12h16 M4 18h16"/><path d="M8 3v6 M16 9v6 M10 15v6" stroke-width="3"/>',
    "git": '<circle cx="6" cy="5" r="2"/><circle cx="6" cy="19" r="2"/><circle cx="18" cy="5" r="2"/><path d="M6 7v10 M18 7v2c0 5-12 1-12 6"/>',
    "close": '<path d="m6 6 12 12 M18 6 6 18"/>',
    "refresh": '<path d="M20 10a8 8 0 1 0-1 8 M20 4v6h-6"/>',
    "plus": '<path d="M12 4v16 M4 12h16"/>',
    "step": '<path d="m4 5 8 7-8 7z M17 5v14"/>',
    "pause": '<path d="M8 5v14 M16 5v14" stroke-width="3"/>',
}


def icon(name, color="#bbc2cb"):
    paths = PATHS.get(name, PATHS["file"]).replace("{color}", color)
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><g fill="none" stroke="{color}" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round">{paths}</g></svg>'
    result = QIcon()
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    for size in [16, 20, 24, 32, 40, 48, 64]:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        result.addPixmap(pixmap)
    return result
