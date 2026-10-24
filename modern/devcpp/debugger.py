from __future__ import annotations
import json
from pathlib import Path
from PySide6.QtCore import QObject, QProcess, Signal
from pygdbmi.gdbmiparser import parse_response


class Debugger(QObject):
    output = Signal(str)
    stopped = Signal(dict)
    variables = Signal(list)
    stack = Signal(list)
    state = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read)
        self.process.readyReadStandardError.connect(lambda: self.output.emit(bytes(self.process.readAllStandardError()).decode("utf-8", "replace")))
        self.process.errorOccurred.connect(lambda _: self.output.emit(self.process.errorString()))
        self.process.finished.connect(lambda *_: self.state.emit("exited"))
        self.process.started.connect(self.initialize)
        self.buffer = b""
        self.token = 0
        self.callbacks = {}
        self.queue = []

    @property
    def active(self):
        return self.process.state() != QProcess.ProcessState.NotRunning

    def start(self, debugger: str, executable: Path, root: Path, breakpoints, arguments):
        if self.active:
            return
        q = lambda text: json.dumps(str(text), ensure_ascii=False)
        self.queue = ["-gdb-set mi-async on", "-gdb-set pagination off", "-gdb-set confirm off",
                      "-file-exec-and-symbols " + q(executable),
                      "-exec-arguments " + " ".join(q(a) for a in arguments)]
        # A temporary main breakpoint gives a useful first stop even without user breakpoints.
        self.queue.append("-break-insert -t main")
        self.queue += ["-break-insert " + q(f"{path}:{line}") for path, line in breakpoints]
        self.queue.append("-exec-run")
        self.buffer = b""
        self.callbacks.clear()
        self.process.setWorkingDirectory(str(root))
        self.process.start(debugger, ["--interpreter=mi2", "--quiet", "--nx"])

    def initialize(self):
        self.next_initial()

    def next_initial(self, record=None):
        if record and record.get("message") == "error":
            self.output.emit(str(record.get("payload")) + "\n")
            self.queue.clear()
            self.stop()
            return
        if self.queue:
            self.command(self.queue.pop(0), self.next_initial)

    def command(self, command, callback=None):
        if not self.active:
            return
        self.token += 1
        if callback:
            self.callbacks[self.token] = callback
        self.process.write(f"{self.token}{command}\n".encode("utf-8"))

    def read(self):
        self.buffer += bytes(self.process.readAllStandardOutput())
        while b"\n" in self.buffer:
            line, self.buffer = self.buffer.split(b"\n", 1)
            try:
                record = parse_response(line.decode("utf-8", "replace").rstrip("\r"))
            except Exception:
                self.output.emit(line.decode("utf-8", "replace") + "\n")
                continue
            payload = record.get("payload") or {}
            if record["type"] == "result":
                callback = self.callbacks.pop(record.get("token"), None)
                if callback:
                    callback(record)
                elif record.get("message") == "error":
                    self.output.emit(str(payload) + "\n")
            elif record.get("message") == "stopped":
                self.state.emit(payload.get("reason", "stopped"))
                self.stopped.emit(payload)
                if not payload.get("reason", "").startswith("exited"):
                    self.refresh()
            elif record.get("message") == "running":
                self.state.emit("running")
            elif record["type"] in ("console", "target", "log", "output"):
                self.output.emit(str(payload))

    def refresh(self):
        self.command("-stack-list-variables --simple-values", lambda r: self.variables.emit((r.get("payload") or {}).get("variables", [])))
        self.command("-stack-list-frames", lambda r: self.stack.emit((r.get("payload") or {}).get("stack", [])))

    def stop(self):
        if self.active:
            self.command("-gdb-exit")
            if not self.process.waitForFinished(1500):
                self.process.kill()
                self.process.waitForFinished(1000)
