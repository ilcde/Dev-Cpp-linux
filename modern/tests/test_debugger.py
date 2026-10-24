import shutil
import subprocess
import time
import pytest
from PySide6.QtWidgets import QApplication
from devcpp.debugger import Debugger


@pytest.mark.skipif(not shutil.which("gcc") or not shutil.which("gdb"), reason="GCC/GDB unavailable")
def test_gdb_breakpoint_variables_stack_and_continue(tmp_path):
    app = QApplication.instance() or QApplication([])
    source = tmp_path / "main.c"
    source.write_text("int main(void) {\n  int answer = 42;\n  answer += 1;\n  return answer == 43 ? 0 : 1;\n}\n")
    binary = tmp_path / "app.exe"
    subprocess.run(["gcc", "-g", "-O0", str(source), "-o", str(binary)], check=True, capture_output=True)
    debugger = Debugger()
    stops, variables, stacks, outputs = [], [], [], []
    debugger.stopped.connect(stops.append)
    debugger.variables.connect(variables.append)
    debugger.stack.connect(stacks.append)
    debugger.output.connect(outputs.append)

    def wait(predicate):
        end = time.monotonic() + 15
        while time.monotonic() < end:
            app.processEvents()
            if predicate():
                return
            time.sleep(.01)
        raise AssertionError("GDB timeout: " + repr(outputs))

    try:
        debugger.start("gdb", binary, tmp_path, [(source, 3)], [])
        wait(lambda: len(stops) >= 1 and bool(stacks))
        assert stops[0]["frame"]["func"] == "main"
        debugger.command("-exec-continue")
        wait(lambda: len(stops) >= 2 and any(any(v.get("value") == "42" for v in group) for group in variables))
        assert stops[1]["reason"] == "breakpoint-hit"
        debugger.command("-exec-next")
        wait(lambda: len(stops) >= 3)
        debugger.command("-exec-continue")
        wait(lambda: any(s.get("reason", "").startswith("exited") for s in stops))
    finally:
        debugger.stop()
