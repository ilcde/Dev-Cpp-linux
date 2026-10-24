"""Exercise the packaged IDE with generated code; never use a user's workspace."""
from pathlib import Path
import tempfile
import time
from PySide6.QtCore import QSettings, QTimer
from .app import Window
from .core import Project


def run(app):
    with tempfile.TemporaryDirectory(prefix="devcpp-selftest-") as temporary:
        root = Path(temporary)
        (root / "helper.c").write_text("constexpr int value = 42;\nint answer(void) { return value; }\n")
        (root / "main.cpp").write_text('#include <iostream>\nextern "C" int answer(void);\nint main() { std::cout << "DEVCPP_INTEGRATION_OK" << std::endl; return answer() == 42 ? 0 : 1; }\n')
        project = Project(sources=["main.cpp", "helper.c"])
        project.save(root)
        window = Window(root, QSettings(str(root / "settings.ini"), QSettings.Format.IniFormat))
        window.close_tab(0)
        window.open_file(root / "main.cpp")
        window.trusted = True
        stage = ["build"]
        build_complete = [False]
        # Window.built is connected first. Wait for it to finish constructing
        # ConPTY widgets; Windows may pump events reentrantly during that step.
        window.build_job.finished.connect(lambda *_: build_complete.__setitem__(0, True))
        stopped, stack, debug_output = [], [], []
        window.debugger.stopped.connect(stopped.append)
        window.debugger.stack.connect(stack.append)
        window.debugger.output.connect(debug_output.append)
        timer = QTimer()
        started = time.monotonic()

        def finish(ok, message):
            timer.stop()
            log = Path.cwd() / "devcpp-self-test.log"
            log.write_text(message + "\n" + window.output.toPlainText() + "\n" + "".join(debug_output), encoding="utf-8")
            window.close()
            app.exit(0 if ok else 1)

        def poll():
            if time.monotonic() - started > 45:
                finish(False, "Timed out at " + stage[0])
            elif stage[0] == "build" and build_complete[0]:
                if not window.run_terminal:
                    finish(False, "Build did not start program")
                elif "DEVCPP_INTEGRATION_OK" in "\n".join(window.run_terminal.screen.display):
                    stage[0] = "debug"
                    window.debugger.start("gdb", project.output(root), root, [], [])
            elif stage[0] == "debug" and stopped and stack:
                finish(stopped[0].get("frame", {}).get("func") == "main", "Packaged build, terminal run and GDB stack check completed")

        window.error = lambda text: finish(False, text)
        timer.timeout.connect(poll)
        window.show()
        timer.start(50)
        QTimer.singleShot(0, lambda: window.build("run"))
        return app.exec()
