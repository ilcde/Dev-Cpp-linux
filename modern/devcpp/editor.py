from __future__ import annotations
import os
import re
from pathlib import Path
from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QColor, QFont, QPainter, QSyntaxHighlighter, QTextCharFormat, QTextCursor, QTextFormat
from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit


class Highlighter(QSyntaxHighlighter):
    def highlightBlock(self, text):
        rules = [(r'\b(?:int|float|double|char|void|bool|auto|const|constexpr|static|struct|class|public|private|protected|return|if|else|for|while|switch|case|break|continue|namespace|using|template|typename|virtual|override|nullptr|true|false|new|delete|unsigned|long|short|include|define|enum|typedef|sizeof|try|catch|throw|noexcept|concept|requires|co_await)\b', "#c4a7ff"),
                 (r'\b\d+(?:\.\d+)?\b', "#f7c87c"),
                 (r'"(?:[^"\\]|\\.)*"|\x27(?:[^\x27\\]|\\.)*\x27', "#92d8be"),
                 (r'//.*$', "#7385a0")]
        for pattern, color in rules:
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)
        self.setCurrentBlockState(0)
        start = 0 if self.previousBlockState() == 1 else text.find("/*")
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#7385a0"))
        while start >= 0:
            end = text.find("*/", start + (0 if self.previousBlockState() == 1 and start == 0 else 2))
            if end < 0:
                self.setCurrentBlockState(1)
                self.setFormat(start, len(text) - start, fmt)
                break
            self.setFormat(start, end + 2 - start, fmt)
            start = text.find("/*", end + 2)


class Gutter(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.gutter_width(), 0)

    def paintEvent(self, event):
        self.editor.paint_gutter(event)

    def mousePressEvent(self, event):
        block = self.editor.firstVisibleBlock()
        while block.isValid():
            rect = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset())
            if rect.top() <= event.position().y() < rect.bottom():
                line = block.blockNumber() + 1
                if line in self.editor.breakpoints:
                    self.editor.breakpoints.remove(line)
                else:
                    self.editor.breakpoints.add(line)
                self.update()
                break
            block = block.next()


class Editor(QPlainTextEdit):
    def __init__(self, path: Path | None = None):
        super().__init__()
        self.setObjectName("codeEditor")
        self.path = path
        self.encoding = "utf-8"
        self.newline = "\n"
        self.breakpoints = set()
        self.execution_line = 0
        self.setFont(QFont("Cascadia Mono" if os.name == "nt" else "monospace", 12))
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.highlighter = Highlighter(self.document())
        self.gutter = Gutter(self)
        self.blockCountChanged.connect(self.update_margin)
        self.updateRequest.connect(self.update_gutter)
        self.cursorPositionChanged.connect(self.highlight_line)
        self.textChanged.connect(self.on_edit)
        self.update_margin()
        if path:
            raw = path.read_bytes()
            self.encoding = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8"
            content = raw.decode(self.encoding)  # Never silently replace and overwrite source bytes.
            self.newline = "\r\n" if "\r\n" in content else "\n"
            self.setPlainText(content.replace("\r\n", "\n"))
        self.document().setModified(False)
        self.highlight_line()

    def on_edit(self):
        # Clear stale locations after edits rather than silently breaking on a different statement.
        self.breakpoints.clear()
        self.execution_line = 0
        self.gutter.update()

    def gutter_width(self):
        return 30 + self.fontMetrics().horizontalAdvance("9") * len(str(self.blockCount()))

    def update_margin(self, *_):
        self.setViewportMargins(self.gutter_width(), 0, 0, 0)

    def update_gutter(self, rect, dy):
        if dy:
            self.gutter.scroll(0, dy)
        else:
            self.gutter.update(0, rect.y(), self.gutter.width(), rect.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        rect = self.contentsRect()
        self.gutter.setGeometry(QRect(rect.left(), rect.top(), self.gutter_width(), rect.height()))

    def paint_gutter(self, event):
        painter = QPainter(self.gutter)
        painter.fillRect(event.rect(), QColor(32, 33, 36, 210))
        block = self.firstVisibleBlock()
        while block.isValid():
            top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
            height = int(self.blockBoundingRect(block).height())
            if top > event.rect().bottom():
                break
            line = block.blockNumber() + 1
            if block.isVisible() and top + height >= event.rect().top():
                painter.setPen(QColor("#7e91ae"))
                painter.drawText(18, top, self.gutter.width() - 24, height, Qt.AlignmentFlag.AlignRight, str(line))
                if line in self.breakpoints:
                    painter.setBrush(QColor("#fb7185"))
                    painter.drawEllipse(3, top + 4, 9, 9)
                if line == self.execution_line:
                    painter.setPen(QColor("#fbbf24"))
                    painter.drawText(2, top, 14, height, Qt.AlignmentFlag.AlignLeft, "▶")
            block = block.next()

    def highlight_line(self):
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor(108, 146, 210, 22))
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        self.setExtraSelections([selection])

    def goto(self, line):
        cursor = QTextCursor(self.document().findBlockByNumber(max(0, line - 1)))
        self.setTextCursor(cursor)
        self.centerCursor()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Tab:
            self.insertPlainText("    ")
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            before = self.textCursor().block().text()[:self.textCursor().positionInBlock()]
            indent = re.match(r"\s*", before).group()
            super().keyPressEvent(event)
            self.insertPlainText(indent + ("    " if before.rstrip().endswith("{") else ""))
        else:
            super().keyPressEvent(event)
