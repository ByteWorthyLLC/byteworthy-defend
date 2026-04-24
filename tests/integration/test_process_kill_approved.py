import subprocess
import time

from bw_defend.security.process_control import kill_process


def test_process_kill_with_approval() -> None:
    proc = subprocess.Popen(["sleep", "30"])
    try:
        result = kill_process(proc.pid, approve=True)
        assert result["killed"] is True
        time.sleep(0.1)
        proc.poll()
        assert proc.returncode is not None
    finally:
        if proc.poll() is None:
            proc.terminate()
