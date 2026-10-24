from __future__ import annotations
import codecs
import os
import signal
import subprocess
from pathlib import Path
from PySide6.QtCore import QObject, QProcess, Signal
from .runtime import process_environment


class Job(QObject):
    output = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = QProcess(self)
        self.process.setProcessEnvironment(process_environment())
        if os.name != "nt":
            params = QProcess.UnixProcessParameters()
            params.flags = QProcess.UnixProcessFlag.CreateNewSession
            self.process.setUnixProcessParameters(params)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read)
        self.process.finished.connect(self.done)
        self.process.errorOccurred.connect(self.error)
        self.pending = []
        self.active = False
        self.text = ""

    def start(self, commands: list[list[str]], root: Path):
        if self.active:
            return False
        self.active = True
        self.text = ""
        self.pending = list(commands)
        self.process.setWorkingDirectory(str(root))
        self.next()
        return True

    def next(self):
        if not self.pending:
            self.finish(True)
            return
        command = self.pending.pop(0)
        self.decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self.process.start(command[0], command[1:])

    def read(self):
        value = self.decoder.decode(bytes(self.process.readAllStandardOutput()))
        self.text += value
        self.output.emit(value)

    def done(self, code, status):
        self.read()
        tail = self.decoder.decode(b"", final=True)
        self.text += tail
        if tail:
            self.output.emit(tail)
        if self.active:
            if code == 0 and status == QProcess.ExitStatus.NormalExit:
                self.next()
            else:
                self.finish(False)

    def error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.text += self.process.errorString()
            self.output.emit(self.process.errorString())
            self.finish(False)

    def finish(self, ok):
        if self.active:
            self.active = False
            self.pending.clear()
            self.finished.emit(ok, self.text)

    def stop(self):
        self.pending.clear()
        if self.process.state() != QProcess.ProcessState.NotRunning:
            pid = int(self.process.processId())
            if pid:
                try:
                    if os.name == "nt":
                        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, timeout=3,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
                    else:
                        os.killpg(pid, signal.SIGTERM)
                except (OSError, subprocess.TimeoutExpired):
                    pass
            self.process.kill()
            self.process.waitForFinished(1500)
        self.finish(False)
