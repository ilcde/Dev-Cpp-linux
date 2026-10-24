import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import sys
import time
import subprocess
import shutil
from pathlib import Path
import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QMessageBox
from devcpp.app import Window
from devcpp.appearance import STYLE
from devcpp.jobs import Job
from devcpp.terminal import Terminal


@pytest.fixture(scope="session")
def app():
    application = QApplication.instance() or QApplication([])
    application.setStyleSheet(STYLE)
    return application


def wait(app, predicate, timeout=10):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        app.processEvents()
        if predicate():
            return
        time.sleep(.01)
    raise AssertionError("Timed out")


@pytest.fixture
def window(app, tmp_path):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    win = Window(tmp_path, settings)
    win.show()
    yield win
    for index in range(win.editors.count()):
        win.editors.widget(index).document().setModified(False)
    win.close()
    app.processEvents()


def test_editor_unicode_bom_crlf_and_save(window, tmp_path):
    path = tmp_path / "tiếng Việt.cpp"
    path.write_bytes('\ufeff// Xin chào\r\nint main() {}\r\n'.encode())
    editor = window.open_file(path)
    assert "Xin chào" in editor.toPlainText()
    editor.insertPlainText("// test\n")
    assert window.save_editor(editor)
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")
    assert b"\r\n" in path.read_bytes()
    assert not editor.document().isModified()


def test_cancel_tab_close_preserves_changes(window, monkeypatch):
    editor = window.editor()
    editor.insertPlainText("unsaved")
    monkeypatch.setattr(QMessageBox, "question", lambda *a: QMessageBox.StandardButton.Cancel)
    count = window.editors.count()
    window.close_tab(window.editors.currentIndex())
    assert window.editors.count() == count
    assert editor.document().isModified()


def test_process_failure_stops_pipeline(app, tmp_path):
    job = Job()
    results = []
    job.finished.connect(lambda ok, text: results.append((ok, text)))
    marker = tmp_path / "should-not-exist"
    job.start([[sys.executable, "-c", "raise SystemExit(3)"], [sys.executable, "-c", f"open({str(marker)!r}, 'w').close()"]], tmp_path)
    wait(app, lambda: bool(results))
    assert results[0][0] is False
    assert not marker.exists()


def test_missing_tool_reports_failure(app, tmp_path):
    job = Job()
    results = []
    job.finished.connect(lambda ok, text: results.append((ok, text)))
    job.start([["devcpp-tool-that-does-not-exist"]], tmp_path)
    wait(app, lambda: bool(results))
    assert results[0][0] is False
    assert results[0][1]


def test_terminal_real_shell(app, tmp_path):
    terminal = Terminal(tmp_path)
    output = []
    terminal.received.connect(output.append)
    try:
        terminal.write(("Write-Output ('DEVCPP_' + 'TERMINAL_OK')" if os.name == "nt" else "printf '%s%s\\n' DEVCPP_ TERMINAL_OK") + "\r")
        wait(app, lambda: "DEVCPP_TERMINAL_OK" in "".join(output), timeout=15)
        terminal.write("echo SECOND_COMMAND\r")
        wait(app, lambda: "SECOND_COMMAND" in "".join(output), timeout=15)
    finally:
        terminal.shutdown()


@pytest.mark.skipif(not shutil.which("git"), reason="Git unavailable")
def test_git_stage_commit_unicode_filename(window, app, tmp_path):
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "DevCpp Test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "core.autocrlf", "false"], cwd=tmp_path, check=True)
    source = tmp_path / "tiếng Việt [file].cpp"
    source.write_text("int main() {}\n")
    window.trusted = True
    errors = []
    window.error = errors.append
    window.refresh_git()
    wait(app, lambda: not window.git_job.active)
    item = next(window.git_list.item(i) for i in range(window.git_list.count()) if source.name in window.git_list.item(i).text())
    item.setSelected(True)
    window.git_stage()
    wait(app, lambda: not window.git_job.active)
    window.commit_message.setText("test unicode paths")
    window.git_commit()
    wait(app, lambda: not window.git_job.active)
    assert not errors
    result = subprocess.run(["git", "show", "HEAD:" + source.name], cwd=tmp_path, capture_output=True, check=True)
    assert result.stdout == source.read_bytes()


def test_debugger_record_views(window):
    window.show_variables([{"name": "answer", "value": "42", "type": "int"}])
    assert window.variables.topLevelItem(0).text(1) == "42"
    window.show_stack([{"level": "0", "func": "main", "file": "main.cpp", "line": "4"}])
    assert window.stack.topLevelItem(0).text(0) == "main"


@pytest.mark.skipif(not shutil.which("g++"), reason="C++ toolchain unavailable")
def test_ui_build_and_run_in_terminal(window, app, tmp_path):
    source = tmp_path / "main.cpp"
    source.write_text('#include <iostream>\nint main() { std::cout << "DEVCPP_RUN_OK" << std::endl; }\n')
    window.close_tab(0)
    window.open_file(source)
    window.trusted = True
    errors = []
    window.error = errors.append
    window.build("run")
    wait(app, lambda: not window.build_job.active, timeout=20)
    assert not errors
    assert window.project.output(tmp_path).is_file()
    assert window.run_terminal is not None
    wait(app, lambda: "DEVCPP_RUN_OK" in "\n".join(window.run_terminal.screen.display), timeout=15)
