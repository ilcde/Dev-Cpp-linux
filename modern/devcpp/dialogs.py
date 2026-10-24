from __future__ import annotations
from dataclasses import fields
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QPlainTextEdit,
                               QCheckBox, QComboBox, QSpinBox, QPushButton, QFileDialog,
                               QColorDialog, QScrollArea, QWidget, QVBoxLayout, QLabel)
from .core import Project


class ProjectDialog(QDialog):
    def __init__(self, project, vi, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Thư viện & cấu hình dự án" if vi else "Libraries & project settings")
        self.resize(680, 730)
        outer = QVBoxLayout(self)
        label = QLabel("Danh sách: mỗi dòng một giá trị. Không cần thêm dấu nháy quanh đường dẫn.\nCMake: chỉnh thư viện trong CMakeLists.txt; nhập executable để Chạy/Debug.\nCác cờ compiler/linker có thể thực thi mã; chỉ dùng cấu hình đáng tin cậy."
                       if vi else "Lists: one value per line; do not quote paths.\nCMake: configure libraries in CMakeLists.txt; set executable for Run/Debug.\nCompiler/linker flags can execute code; use trusted settings only.")
        label.setWordWrap(True)
        outer.addWidget(label)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        form = QFormLayout(body)
        labels = {"compiler_c": "Trình biên dịch C", "compiler_cpp": "Trình biên dịch C++", "debugger": "GDB",
                  "sources": "File nguồn (trống = file hiện tại)", "include_dirs": "Thư mục header (-I)",
                  "library_dirs": "Thư mục thư viện (-L)", "libraries": "Tên thư viện (-l)",
                  "compile_flags": "Cờ biên dịch", "link_flags": "Cờ liên kết / file .a, .lib",
                  "arguments": "Tham số chạy", "standard_c": "Chuẩn C", "standard_cpp": "Chuẩn C++",
                  "executable": "Đường dẫn chương trình đầu ra", "cmake": "Dùng CMake"}
        self.inputs = {}
        for field in fields(project):
            value = getattr(project, field.name)
            if field.name in ("standard_c", "standard_cpp"):
                widget = QComboBox()
                widget.setEditable(True)
                widget.addItems(["c23", "c17", "c11", "c99", "gnu23"] if field.name == "standard_c"
                                else ["c++26", "c++23", "c++20", "c++17", "gnu++26", "c++29"])
                widget.setCurrentText(value)
                widget.setToolTip("C++26 support is experimental in GCC. C++29 requires GCC 17 development builds. Feature availability depends on your compiler and standard library.")
            elif isinstance(value, list):
                widget = QPlainTextEdit("\n".join(value))
                widget.setMaximumHeight(75)
            elif isinstance(value, bool):
                widget = QCheckBox()
                widget.setChecked(value)
            else:
                widget = QLineEdit(value)
            self.inputs[field.name] = widget
            form.addRow(labels[field.name] if vi else field.name.replace("_", " ").title(), widget)
        scroll.setWidget(body)
        outer.addWidget(scroll)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def project(self):
        data = {}
        for name, widget in self.inputs.items():
            if isinstance(widget, QComboBox):
                data[name] = widget.currentText().strip()
            elif isinstance(widget, QPlainTextEdit):
                data[name] = [line.strip() for line in widget.toPlainText().splitlines() if line.strip()]
            elif isinstance(widget, QCheckBox):
                data[name] = widget.isChecked()
            else:
                data[name] = widget.text().strip()
        return Project(**data)


class SettingsDialog(QDialog):
    def __init__(self, settings, vi, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cá nhân hóa" if vi else "Personalization")
        self.resize(620, 420)
        form = QFormLayout(self)
        self.language = QComboBox()
        self.language.addItems(["Tiếng Việt", "English"])
        self.language.setCurrentIndex(0 if vi else 1)
        form.addRow("Ngôn ngữ / Language (restart)", self.language)
        self.path = QLineEdit(settings.value("wallpaper", ""))
        form.addRow("Wallpaper", self.path)
        choose = QPushButton("Chọn ảnh / video" if vi else "Choose image / video")
        choose.clicked.connect(self.choose)
        form.addRow("", choose)
        self.color = QLineEdit(settings.value("background", "#202124"))
        color = QPushButton("Màu nền" if vi else "Background color")
        color.clicked.connect(self.choose_color)
        form.addRow(color, self.color)
        self.opacity = QSpinBox()
        self.opacity.setRange(0, 100)
        self.opacity.setValue(int(settings.value("opacity", 22)))
        self.opacity.setSuffix(" %")
        form.addRow("Độ hiện nền" if vi else "Wallpaper opacity", self.opacity)
        self.rpc = QCheckBox("Discord Rich Presence")
        self.rpc.setChecked(settings.value("rpc_enabled", False, type=bool))
        form.addRow(self.rpc)
        self.client = QLineEdit(settings.value("rpc_id", ""))
        form.addRow("Discord Application ID", self.client)
        hint = QLabel("RPC chỉ chia sẻ trạng thái 'C / C++ — Dev-C++ Modern'.\nKhông gửi tên dự án, file hoặc đường dẫn. Video nền không phát âm thanh."
                      if vi else "RPC shares only 'C / C++ — Dev-C++ Modern'.\nNo project names, files or paths. Wallpaper videos play without audio.")
        hint.setWordWrap(True)
        form.addRow(hint)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def choose(self):
        path, _ = QFileDialog.getOpenFileName(self, "Wallpaper", "", "Media (*.png *.jpg *.jpeg *.webp *.bmp *.mp4 *.webm *.mkv *.mov)")
        if path:
            self.path.setText(path)

    def choose_color(self):
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self.color.setText(color.name())
