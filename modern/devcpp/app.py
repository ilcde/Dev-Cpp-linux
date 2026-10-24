from __future__ import annotations
import json
import argparse
import os
from pathlib import Path
import sys
import tempfile
from PySide6.QtCore import Qt, QSettings, QDir, QTimer, QSize
from PySide6.QtGui import QAction, QColor, QTextCursor
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSplitter, QTabWidget, QTreeView, QListWidget, QListWidgetItem, QTreeWidget,
    QTreeWidgetItem, QPlainTextEdit, QPushButton, QLineEdit, QFileDialog, QMessageBox,
    QDialog, QInputDialog, QToolBar, QFileSystemModel, QToolButton, QTabBar, QSizePolicy)
from .core import Project, atomic_write, git_entries
from .jobs import Job
from .editor import Editor
from .terminal import Terminal
from .debugger import Debugger
from .appearance import Background, Presence, STYLE, PanelTabs
from .dialogs import ProjectDialog, SettingsDialog
from .icons import icon, application_icon
from .runtime import prepare_runtime
from .legacy import import_project, template_catalog, create_project


class Window(QMainWindow):
    def __init__(self, root=None, settings=None):
        super().__init__()
        self.settings = settings or QSettings("DevCpp", "Modern")
        self.vi = self.settings.value("language", "vi") == "vi"
        self.root = Path(root or Path.home()).resolve()
        self.project = Project()
        self.trusted = False
        self.git_callback = None
        self.build_after = None
        self.run_terminal = None
        self.resize(1280, 820)
        self.setMinimumSize(950, 640)
        self.setWindowTitle("Dev-C++ Modern • " + self.root.name)
        self.setWindowIcon(application_icon())
        self.background = Background()
        self.setCentralWidget(self.background)
        layout = QVBoxLayout(self.background)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.workspace_label = QLabel(self.root.name)
        self.workspace_label.setObjectName("muted")
        self.main_split = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(self.main_split, 1)
        self.sidebar = PanelTabs()
        self.sidebar.setObjectName("sidebar")
        self.main_split.addWidget(self.sidebar)
        self.files = QTreeView()
        self.model = QFileSystemModel(self)
        self.model.setFilter(QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot)
        self.files.setModel(self.model)
        for column in (1, 2, 3):
            self.files.hideColumn(column)
        self.files.setHeaderHidden(True)
        self.files.doubleClicked.connect(lambda index: self.open_file(Path(self.model.filePath(index))) if not self.model.isDir(index) else None)
        self.sidebar.addTab(self.files, icon("folder"), self.t("Tệp", "Files"))
        self.create_git_panel()
        self.work_split = QSplitter(Qt.Orientation.Vertical)
        self.main_split.addWidget(self.work_split)
        self.editors = PanelTabs()
        self.editors.setObjectName("editorTabs")
        self.editors.setTabsClosable(False)
        self.editors.setDocumentMode(True)
        self.editors.setMovable(True)
        self.editors.tabCloseRequested.connect(self.close_tab)
        self.work_split.addWidget(self.editors)
        self.panels = PanelTabs()
        self.panels.setObjectName("toolPanels")
        self.work_split.addWidget(self.panels)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.document().setMaximumBlockCount(10000)
        self.panels.addTab(self.output, icon("build"), self.t("Biên dịch", "Build"))
        self.terminals = PanelTabs()
        self.terminals.setTabsClosable(False)
        self.terminals.setDocumentMode(True)
        for tabs in (self.sidebar, self.editors, self.panels, self.terminals):
            tabs.tabBar().setDrawBase(False)
        self.terminals.tabCloseRequested.connect(self.close_terminal)
        terminal_panel = QWidget()
        terminal_panel.setObjectName("toolPanel")
        terminal_layout = QVBoxLayout(terminal_panel)
        terminal_layout.setContentsMargins(0, 0, 0, 0)
        new_terminal = QToolButton()
        new_terminal.setIcon(icon("plus"))
        new_terminal.setToolTip(self.t("Terminal mới (Ctrl+`)", "New terminal (Ctrl+`)"))
        new_terminal.clicked.connect(self.new_terminal)
        self.terminals.setCornerWidget(new_terminal)
        terminal_layout.addWidget(self.terminals)
        self.panels.addTab(terminal_panel, icon("terminal"), "Terminal")
        self.create_debug_panel()
        self.main_split.setSizes([220, 1060])
        self.work_split.setSizes([550, 200])
        self.build_job = Job(self)
        self.build_job.output.connect(self.log)
        self.build_job.finished.connect(self.built)
        self.git_job = Job(self)
        self.git_job.finished.connect(self.git_done)
        self.debugger = Debugger(self)
        self.debugger.output.connect(self.debug_log.insertPlainText)
        self.debugger.stopped.connect(self.debug_stopped)
        self.debugger.variables.connect(self.show_variables)
        self.debugger.stack.connect(self.show_stack)
        self.debugger.state.connect(lambda state: self.statusBar().showMessage("Debug: " + state))
        self.presence = Presence(self)
        self.presence.status.connect(self.statusBar().showMessage)
        self.background.error.connect(self.log)
        self.actions()
        self.apply_appearance()
        self.set_workspace(self.root)
        self.new_file()
        self.statusBar().showMessage(self.t("Sẵn sàng", "Ready"))
        self.language_status = QLabel("UTF-8   |   C23 / C++26   ")
        self.statusBar().addPermanentWidget(self.language_status)

    def t(self, vi, en):
        return vi if self.vi else en

    def action(self, menu, label, callback, shortcut=None, symbol=None):
        action = QAction(label, self)
        if symbol:
            action.setIcon(icon(symbol, "#85c8a0" if symbol == "run" else "#dc8d8d" if symbol == "stop" else "#bbc2cb"))
        action.setToolTip(label + (f" ({shortcut})" if shortcut else ""))
        action.triggered.connect(callback)
        if shortcut:
            action.setShortcut(shortcut)
        menu.addAction(action)
        return action

    def actions(self):
        file = self.menuBar().addMenu(self.t("Tệp", "File"))
        new_action = self.action(file, self.t("Tệp mới", "New file"), self.new_file, "Ctrl+N", "file")
        self.action(file, self.t("Dự án từ template gốc…", "New project from upstream template…"), self.new_project, symbol="folder")
        self.action(file, self.t("Nhập dự án Dev-C++ (.dev)…", "Import Dev-C++ project (.dev)…"), self.import_dev, symbol="folder")
        self.action(file, self.t("Mở tệp…", "Open file…"), self.open_dialog, "Ctrl+O")
        folder_action = self.action(file, self.t("Mở thư mục…", "Open folder…"), self.choose_workspace, "Ctrl+Shift+O", "folder")
        save_action = self.action(file, self.t("Lưu", "Save"), self.save_current, "Ctrl+S", "save")
        self.action(file, self.t("Lưu thành…", "Save as…"), lambda: self.save_editor(self.editor(), True), "Ctrl+Shift+S")
        self.action(file, self.t("Thoát", "Quit"), self.close, "Alt+F4")
        edit = self.menuBar().addMenu(self.t("Soạn thảo", "Edit"))
        for vi, en, method, shortcut in [("Hoàn tác", "Undo", "undo", "Ctrl+Z"), ("Làm lại", "Redo", "redo", "Ctrl+Y"),
                                         ("Cắt", "Cut", "cut", "Ctrl+X"), ("Sao chép", "Copy", "copy", "Ctrl+C"),
                                         ("Dán", "Paste", "paste", "Ctrl+V")]:
            self.action(edit, self.t(vi, en), lambda checked=False, m=method: getattr(QApplication.focusWidget(), m, lambda: None)(), shortcut)
        self.action(edit, self.t("Tìm…", "Find…"), self.find, "Ctrl+F")
        self.action(edit, self.t("Đến dòng…", "Go to line…"), self.goto, "Ctrl+G")
        project = self.menuBar().addMenu(self.t("Dự án", "Project"))
        self.action(project, self.t("Thư viện & toolchain…", "Libraries & toolchain…"), self.project_settings)
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.addToolBar(toolbar)
        toolbar.addActions([new_action, folder_action, save_action])
        toolbar.addSeparator()
        for vi, en, callback, shortcut in [("Biên dịch", "Build", lambda: self.build(), "F7"),
                                            ("Chạy", "Run", lambda: self.build("run"), "F6"),
                                            ("Debug", "Debug", lambda: self.build("debug"), "F5"),
                                            ("Dừng", "Stop", self.stop, "Shift+F5")]:
            action = self.action(project, self.t(vi, en), callback, shortcut, en.lower())
            toolbar.addAction(action)
            if en in ("Build", "Run", "Debug"):
                toolbar.widgetForAction(action).setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        toolbar.addSeparator()
        toolbar.addAction(self.action(project, self.t("Terminal mới", "New terminal"), self.new_terminal, "Ctrl+`", "terminal"))
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        toolbar.addWidget(self.workspace_label)
        toolbar.addSeparator()
        preferences = self.menuBar().addMenu(self.t("Giao diện", "Appearance"))
        toolbar.addAction(self.action(preferences, self.t("Cá nhân hóa…", "Personalize…"), self.preferences, symbol="settings"))

    def create_git_panel(self):
        panel = QWidget()
        panel.setObjectName("toolPanel")
        layout = QVBoxLayout(panel)
        self.git_list = QListWidget()
        self.git_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.git_list)
        for vi, en, callback in [("Làm mới", "Refresh", self.refresh_git), ("Xem diff", "View diff", self.git_diff),
                                  ("Stage mục đã chọn", "Stage selected", self.git_stage), ("Bỏ stage mục đã chọn", "Unstage selected", self.git_unstage)]:
            button = QPushButton(self.t(vi, en))
            button.setIcon(icon({"Refresh": "refresh", "View diff": "file", "Stage selected": "plus", "Unstage selected": "close"}[en]))
            button.clicked.connect(callback)
            layout.addWidget(button)
        self.commit_message = QLineEdit()
        self.commit_message.setPlaceholderText(self.t("Nội dung commit", "Commit message"))
        layout.addWidget(self.commit_message)
        commit = QPushButton("Commit")
        commit.setIcon(icon("git"))
        commit.clicked.connect(self.git_commit)
        layout.addWidget(commit)
        self.sidebar.addTab(panel, icon("git"), "Git")
        self.git_diff_view = None

    def create_debug_panel(self):
        panel = QWidget()
        panel.setObjectName("toolPanel")
        layout = QVBoxLayout(panel)
        buttons = QHBoxLayout()
        for vi, en, cmd in [("Tiếp tục", "Continue", "-exec-continue"), ("Bước qua", "Step over", "-exec-next"),
                            ("Bước vào", "Step into", "-exec-step"), ("Bước ra", "Step out", "-exec-finish"), ("Tạm dừng", "Pause", "-exec-interrupt")]:
            button = QPushButton(self.t(vi, en))
            button.setIcon(icon("pause" if en == "Pause" else "run" if en == "Continue" else "step"))
            button.clicked.connect(lambda checked=False, c=cmd: self.debugger.command(c))
            buttons.addWidget(button)
        layout.addLayout(buttons)
        splitter = QSplitter()
        self.variables = QTreeWidget()
        self.variables.setHeaderLabels([self.t("Biến", "Variable"), self.t("Giá trị", "Value"), self.t("Kiểu", "Type")])
        splitter.addWidget(self.variables)
        self.stack = QTreeWidget()
        self.stack.setHeaderLabels(["Stack", self.t("Vị trí", "Location")])
        self.stack.itemDoubleClicked.connect(self.select_frame)
        splitter.addWidget(self.stack)
        self.debug_log = QPlainTextEdit()
        self.debug_log.setReadOnly(True)
        self.debug_log.document().setMaximumBlockCount(5000)
        splitter.addWidget(self.debug_log)
        layout.addWidget(splitter)
        self.watch = QLineEdit()
        self.watch.setPlaceholderText(self.t("Biểu thức cần kiểm tra — Enter", "Evaluate expression — Enter"))
        self.watch.returnPressed.connect(self.evaluate)
        layout.addWidget(self.watch)
        self.panels.addTab(panel, icon("debug"), "Debug")

    def editor(self):
        return self.editors.currentWidget()

    def add_editor(self, editor):
        index = self.editors.addTab(editor, editor.path.name if editor.path else self.t("Chưa lưu.cpp", "Untitled.cpp"))
        self.editors.setTabIcon(index, icon("file", "#79b9c4"))
        close = QToolButton()
        close.setIcon(icon("close"))
        close.setAutoRaise(True)
        close.setFixedSize(20, 20)
        close.setToolTip(self.t("Đóng tệp", "Close file"))
        close.clicked.connect(lambda: self.close_tab(self.editors.indexOf(editor)))
        self.editors.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, close)
        self.editors.setCurrentIndex(index)
        editor.document().modificationChanged.connect(lambda _: self.update_title(editor))
        editor.cursorPositionChanged.connect(lambda: self.cursor_status(editor))
        editor.setFocus()

    def update_title(self, editor):
        index = self.editors.indexOf(editor)
        if index >= 0:
            name = editor.path.name if editor.path else self.t("Chưa lưu.cpp", "Untitled.cpp")
            self.editors.setTabText(index, name + (" •" if editor.document().isModified() else ""))

    def cursor_status(self, editor):
        cursor = editor.textCursor()
        self.statusBar().showMessage(f"UTF-8  •  Ln {cursor.blockNumber() + 1}, Col {cursor.positionInBlock() + 1}  •  {self.root.name}")

    def new_file(self):
        self.add_editor(Editor())

    def open_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, self.t("Mở tệp", "Open file"), str(self.root), "C/C++ (*.c *.cpp *.cc *.cxx *.h *.hpp);;All files (*)")
        if path:
            self.open_file(Path(path))

    def open_file(self, path):
        path = path.resolve()
        for index in range(self.editors.count()):
            editor = self.editors.widget(index)
            if editor.path == path:
                self.editors.setCurrentIndex(index)
                return editor
        try:
            if path.stat().st_size > 8 * 1024 * 1024:
                raise ValueError(self.t("Tệp quá lớn (> 8 MiB).", "File too large (> 8 MiB)."))
            editor = Editor(path)
            self.add_editor(editor)
            return editor
        except (OSError, UnicodeError, ValueError) as exc:
            self.error(str(exc))

    def save_current(self):
        return self.save_editor(self.editor())

    def save_editor(self, editor, save_as=False):
        if not editor:
            return False
        path = editor.path
        if path is None or save_as:
            name, _ = QFileDialog.getSaveFileName(self, self.t("Lưu tệp", "Save file"), str(path or self.root / "main.cpp"), "C/C++ (*.cpp *.c *.h *.hpp);;All files (*)")
            if not name:
                return False
            path = Path(name).resolve()
            for i in range(self.editors.count()):
                other = self.editors.widget(i)
                if other is not editor and other.path == path:
                    self.error(self.t("Tệp đang mở trong tab khác.", "File is open in another tab."))
                    return False
        try:
            text = editor.toPlainText().replace("\n", editor.newline)
            if editor.encoding == "utf-8-sig":
                text = "\ufeff" + text
            atomic_write(path, text)
            editor.path = path
            editor.document().setModified(False)
            self.update_title(editor)
            return True
        except OSError as exc:
            self.error(str(exc))
            return False

    def may_close(self, editor):
        if not editor.document().isModified():
            return True
        answer = QMessageBox.question(self, self.t("Lưu thay đổi?", "Save changes?"), str(editor.path or "Untitled"),
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
        if answer == QMessageBox.StandardButton.Save:
            return self.save_editor(editor)
        return answer == QMessageBox.StandardButton.Discard

    def close_tab(self, index):
        editor = self.editors.widget(index)
        if self.may_close(editor):
            self.editors.removeTab(index)
            editor.deleteLater()

    def choose_workspace(self):
        path = QFileDialog.getExistingDirectory(self, self.t("Mở thư mục", "Open folder"), str(self.root))
        if path:
            self.open_workspace(Path(path))

    def open_workspace(self, path):
        if path.resolve() == self.root:
            return True
        for index in range(self.editors.count()):
            if not self.may_close(self.editors.widget(index)):
                return False
        self.stop()
        self.git_job.stop()
        while self.terminals.count():
            self.close_terminal(0)
        while self.editors.count():
            editor = self.editors.widget(0)
            self.editors.removeTab(0)
            editor.deleteLater()
        self.set_workspace(Path(path))
        return True

    def new_project(self):
        catalog = template_catalog()
        name, ok = QInputDialog.getItem(self, self.t("Template Dev-C++ gốc", "Original Dev-C++ templates"),
                                      self.t("Dự án console", "Console project"), [name for _, name in catalog], 0, False)
        if not ok:
            return
        language, ok = QInputDialog.getItem(self, "C / C++", self.t("Ngôn ngữ", "Language"), ["C++", "C"], 0, False)
        if not ok:
            return
        parent = QFileDialog.getExistingDirectory(self, self.t("Thư mục chứa dự án", "Parent folder"), str(self.root))
        if not parent:
            return
        folder, ok = QInputDialog.getText(self, self.t("Dự án mới", "New project"), self.t("Tên thư mục mới", "New folder name"))
        if not ok or not folder.strip():
            return
        if folder in (".", "..") or any(char in folder for char in '/\\:'):
            self.error(self.t("Tên thư mục không hợp lệ", "Invalid folder name"))
            return
        try:
            template = next(path for path, title in catalog if title == name)
            source = create_project(template, Path(parent) / folder, cpp=language == "C++")
            if self.open_workspace(source.parent):
                self.open_file(source)
        except (OSError, ValueError) as exc:
            self.error(str(exc))

    def import_dev(self):
        path, _ = QFileDialog.getOpenFileName(self, self.t("Nhập dự án gốc", "Import upstream project"), str(self.root), "Dev-C++ (*.dev)")
        if not path:
            return
        from configparser import Error as IniError
        path = Path(path)
        try:
            if (path.parent / "devcpp.json").exists():
                raise ValueError(self.t("devcpp.json đã tồn tại; không ghi đè cấu hình hiện tại.", "devcpp.json already exists; existing settings will not be overwritten."))
            project, warnings = import_project(path)
            review = self.t("Giữ nguyên file .dev. Tạo devcpp.json với các file sau:\n", "Keep the .dev file unchanged. Create devcpp.json with these sources:\n")
            review += "\n".join(project.sources) + "\n\n" + "\n".join(warnings)
            if QMessageBox.question(self, self.t("Kiểm tra cấu hình nhập", "Review import"), review,
                                    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel) != QMessageBox.StandardButton.Ok:
                return
            if self.open_workspace(path.parent):
                project.save(path.parent)
                self.project = project
                for source in project.sources:
                    self.open_file(path.parent / source)
        except (OSError, ValueError, KeyError, IniError) as exc:
            self.error(str(exc))

    def set_workspace(self, root):
        self.root = root.resolve()
        self.trusted = False
        try:
            self.project = Project.load(self.root)
        except (ValueError, OSError) as exc:
            self.project = Project()
            self.error(str(exc))
        self.model.setRootPath(str(self.root))
        self.files.setRootIndex(self.model.index(str(self.root)))
        self.workspace_label.setText(self.root.name)
        self.workspace_label.setToolTip(str(self.root))
        self.setWindowTitle("Dev-C++ Modern • " + self.root.name)
        self.git_list.clear()

    def trust(self):
        if not self.trusted:
            answer = QMessageBox.question(self, self.t("Tin cậy dự án", "Trust workspace"),
                self.t("Build, Git hooks và terminal có thể thực thi mã của dự án. Bạn tin cậy thư mục này?\n", "Builds, Git hooks and terminals can execute project code. Trust this folder?\n") + str(self.root),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            self.trusted = answer == QMessageBox.StandardButton.Yes
        return self.trusted

    def project_settings(self):
        dialog = ProjectDialog(self.project, self.vi, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            project = dialog.project()
            try:
                project.save(self.root)
                self.project = Project.load(self.root)
            except (OSError, ValueError) as exc:
                self.error(str(exc))

    def build(self, after=None):
        if self.build_job.active or self.debugger.active:
            self.error(self.t("Hãy dừng tác vụ hiện tại trước.", "Stop the active task first."))
            return
        if not self.trust():
            return
        for index in range(self.editors.count()):
            editor = self.editors.widget(index)
            if editor.document().isModified() or editor == self.editor() and editor.path is None:
                if not self.save_editor(editor):
                    return
        try:
            self.project = Project.load(self.root)
            commands = self.project.build_commands(self.root, self.editor().path if self.editor() else None)
            if self.project.cmake and after and not self.project.executable:
                raise ValueError(self.t("Đặt executable trong cấu hình dự án CMake trước khi Chạy/Debug.", "Set the CMake executable path in project settings before Run/Debug."))
        except (ValueError, OSError) as exc:
            self.error(str(exc))
            return
        self.build_after = after
        self.output.clear()
        self.panels.setCurrentIndex(0)
        for command in commands:
            self.log("› " + json.dumps(command, ensure_ascii=False) + "\n")
        self.build_job.start(commands, self.root)

    def built(self, ok, text):
        self.log(self.t("\nBiên dịch thành công.\n", "\nBuild succeeded.\n") if ok else self.t("\nBiên dịch thất bại.\n", "\nBuild failed.\n"))
        after, self.build_after = self.build_after, None
        if not ok:
            return
        executable = self.project.output(self.root)
        if after and not executable.is_file():
            self.error(self.t("Không tìm thấy chương trình: ", "Executable not found: ") + str(executable))
            return
        if after == "run":
            terminal = Terminal(self.root, command=[str(executable), *self.project.arguments])
            self.add_terminal(terminal, self.t("Chương trình", "Program"))
            self.terminals.setCurrentWidget(terminal)
            self.run_terminal = terminal
            self.panels.setCurrentIndex(1)
            terminal.setFocus()
        elif after == "debug":
            self.variables.clear()
            self.stack.clear()
            self.debug_log.clear()
            points = [(self.editors.widget(i).path, line) for i in range(self.editors.count())
                      for line in self.editors.widget(i).breakpoints if self.editors.widget(i).path]
            self.panels.setCurrentIndex(2)
            self.debugger.start(self.project.debugger, executable, self.root, points, self.project.arguments)

    def stop(self):
        self.build_after = None
        self.build_job.stop()
        self.debugger.stop()
        if self.run_terminal:
            self.run_terminal.shutdown()
            self.run_terminal = None
        for index in range(self.editors.count()):
            editor = self.editors.widget(index)
            editor.execution_line = 0
            editor.gutter.update()

    def new_terminal(self):
        if not self.trust():
            return None
        terminal = Terminal(self.root)
        self.add_terminal(terminal, f"Shell {self.terminals.count() + 1}")
        self.terminals.setCurrentWidget(terminal)
        self.panels.setCurrentIndex(1)
        terminal.setFocus()
        return terminal

    def add_terminal(self, terminal, title):
        index = self.terminals.addTab(terminal, icon("terminal"), title)
        close = QToolButton()
        close.setIcon(icon("close"))
        close.setFixedSize(20, 20)
        close.setToolTip(self.t("Đóng terminal", "Close terminal"))
        close.clicked.connect(lambda: self.close_terminal(self.terminals.indexOf(terminal)))
        self.terminals.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, close)

    def close_terminal(self, index):
        terminal = self.terminals.widget(index)
        if terminal is self.run_terminal:
            self.run_terminal = None
        terminal.shutdown()
        self.terminals.removeTab(index)
        terminal.deleteLater()

    def git(self, args, callback):
        if self.git_job.active or not self.trust():
            return
        self.git_callback = callback
        self.git_job.start([["git", "--no-pager", "-c", "core.quotepath=false", *args]], self.root)

    def git_done(self, ok, text):
        callback, self.git_callback = self.git_callback, None
        if not ok and callback:
            self.error(text or "Git failed")
        elif callback:
            callback(text)

    def refresh_git(self):
        self.git(["status", "--porcelain=v1", "-z", "--untracked-files=normal"], self.show_git)

    def show_git(self, text):
        self.git_list.clear()
        for status, path in git_entries(text):
            item = QListWidgetItem(f"{status}  {path}")
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.git_list.addItem(item)

    def git_paths(self):
        return [item.data(Qt.ItemDataRole.UserRole) for item in self.git_list.selectedItems()]

    def git_stage(self):
        paths = self.git_paths()
        if paths and self.trust():
            self.git(["--literal-pathspecs", "add", "--", *paths], lambda _: self.refresh_git())

    def git_unstage(self):
        paths = self.git_paths()
        if paths and self.trust():
            self.git(["--literal-pathspecs", "restore", "--staged", "--", *paths], lambda _: self.refresh_git())

    def git_diff(self):
        paths = self.git_paths()
        choices = [self.t("Chưa stage", "Unstaged"), self.t("Đã stage", "Staged")]
        choice, ok = QInputDialog.getItem(self, "Git diff", self.t("So sánh", "Compare"), choices, editable=False)
        if ok:
            self.git(["--literal-pathspecs", "diff", "--no-ext-diff", "--no-textconv", *(["--cached"] if choice == choices[1] else []), "--", *paths], self.show_diff)

    def show_diff(self, text):
        dialog = QDialog(self)
        dialog.setWindowTitle("Git diff")
        dialog.resize(1000, 650)
        layout = QVBoxLayout(dialog)
        view = QPlainTextEdit(text or self.t("Không có diff chưa stage. Tệp mới chưa được Git theo dõi.", "No unstaged diff. New files are not tracked yet."))
        view.setReadOnly(True)
        layout.addWidget(view)
        dialog.exec()

    def git_commit(self):
        message = self.commit_message.text().strip()
        if message and self.trust():
            self.git(["commit", "-m", message], self.committed)

    def committed(self, text):
        self.commit_message.clear()
        self.log(text)
        self.refresh_git()

    def debug_stopped(self, payload):
        for index in range(self.editors.count()):
            editor = self.editors.widget(index)
            editor.execution_line = 0
            editor.gutter.update()
        frame = payload.get("frame", {})
        self.show_frame(frame)

    def show_frame(self, frame):
        path = frame.get("fullname") or frame.get("file")
        if path:
            editor = self.open_file((self.root / path).resolve())
            if editor:
                editor.execution_line = int(frame.get("line", 1))
                editor.goto(editor.execution_line)
                editor.gutter.update()

    def show_variables(self, variables):
        self.variables.clear()
        for var in variables:
            QTreeWidgetItem(self.variables, [var.get("name", ""), var.get("value", ""), var.get("type", "")])

    def show_stack(self, frames):
        self.stack.clear()
        for entry in frames:
            frame = entry.get("frame", entry)
            item = QTreeWidgetItem(self.stack, [frame.get("func", "?"), f"{frame.get('file', '')}:{frame.get('line', '')}"])
            item.setData(0, Qt.ItemDataRole.UserRole, frame)

    def select_frame(self, item, column):
        frame = item.data(0, Qt.ItemDataRole.UserRole)
        self.debugger.command("-stack-select-frame " + str(int(frame.get("level", 0))), lambda _: self.debugger.refresh())
        self.show_frame(frame)

    def evaluate(self):
        expression = self.watch.text().strip()
        if expression:
            self.debugger.command("-data-evaluate-expression " + json.dumps(expression, ensure_ascii=False),
                lambda record: self.debug_log.appendPlainText(expression + " = " + str(record.get("payload"))))

    def find(self):
        editor = self.editor()
        if editor:
            text, ok = QInputDialog.getText(self, self.t("Tìm", "Find"), self.t("Nội dung", "Text"))
            if ok and text and not editor.find(text):
                editor.moveCursor(QTextCursor.MoveOperation.Start)
                editor.find(text)

    def goto(self):
        editor = self.editor()
        if editor:
            line, ok = QInputDialog.getInt(self, self.t("Đến dòng", "Go to line"), "Line", 1, 1, editor.blockCount())
            if ok:
                editor.goto(line)

    def preferences(self):
        dialog = SettingsDialog(self.settings, self.vi, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        if not QColor(dialog.color.text()).isValid():
            self.error(self.t("Màu nền không hợp lệ.", "Invalid background color."))
            return
        if dialog.rpc.isChecked() and not dialog.client.text().strip().isdigit():
            self.error("Discord Application ID must contain digits.")
            return
        for key, value in {"language": "vi" if dialog.language.currentIndex() == 0 else "en",
                           "wallpaper": dialog.path.text().strip(), "background": dialog.color.text(),
                           "opacity": dialog.opacity.value(), "rpc_enabled": dialog.rpc.isChecked(),
                           "rpc_id": dialog.client.text().strip()}.items():
            self.settings.setValue(key, value)
        self.settings.sync()
        self.apply_appearance()

    def apply_appearance(self):
        self.background.configure(self.settings.value("wallpaper", ""), self.settings.value("background", "#202124"), int(self.settings.value("opacity", 22)) / 100)
        self.presence.start(self.settings.value("rpc_id", "") if self.settings.value("rpc_enabled", False, type=bool) else "")

    def changeEvent(self, event):
        super().changeEvent(event)
        if hasattr(self, "background"):
            from PySide6.QtCore import QEvent
            if event.type() == QEvent.Type.WindowStateChange and not self.background.player.source().isEmpty():
                if self.isMinimized():
                    self.background.player.pause()
                else:
                    self.background.player.play()

    def log(self, text):
        self.output.moveCursor(QTextCursor.MoveOperation.End)
        self.output.insertPlainText(text)

    def error(self, text):
        QMessageBox.warning(self, "Dev-C++ Modern", text)

    def closeEvent(self, event):
        for index in range(self.editors.count()):
            if not self.may_close(self.editors.widget(index)):
                event.ignore()
                return
        self.stop()
        self.git_callback = None
        self.git_job.stop()
        while self.terminals.count():
            self.close_terminal(0)
        self.background.player.stop()
        self.presence.stop()
        event.accept()


def main():
    parser = argparse.ArgumentParser(description="Dev-C++ Modern")
    parser.add_argument("workspace", nargs="?", default=str(Path.cwd()))
    parser.add_argument("--smoke-test", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--self-test", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    app.setWindowIcon(application_icon())
    if os.name == "nt":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ilcde.DevCpp.Modern")
    prepare_runtime()
    if args.self_test:
        from .selftest import run
        return run(app)
    root = Path(args.workspace).resolve()
    if not root.is_dir():
        QMessageBox.critical(None, "Dev-C++ Modern", "Workspace is not a directory: " + str(root))
        return 1
    temporary_settings = tempfile.TemporaryDirectory() if args.smoke_test else None
    settings = QSettings(str(Path(temporary_settings.name) / "settings.ini"), QSettings.Format.IniFormat) if temporary_settings else None
    window = Window(root, settings)
    window.show()
    if args.smoke_test:
        QTimer.singleShot(1000, window.close)
    result = app.exec()
    if temporary_settings:
        temporary_settings.cleanup()
    return result


if __name__ == "__main__":
    sys.exit(main())
