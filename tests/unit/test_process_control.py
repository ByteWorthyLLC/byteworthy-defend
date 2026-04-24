import subprocess

import pytest

from bw_defend.security.process_control import _list_processes_unix, _list_processes_windows, list_processes


def test_list_processes_limit_validation() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        list_processes(limit=0)


def test_unix_process_listing_parses_ps_output(monkeypatch) -> None:
    mock_output = "1001 python3 00:01:10\n1002 bw-defend 00:00:09\n"

    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args=args, returncode=0, stdout=mock_output, stderr="")

    monkeypatch.setattr("bw_defend.security.process_control.subprocess.run", mock_run)

    items = _list_processes_unix(limit=1)
    assert items == [{"pid": "1001", "command": "python3", "etime": "00:01:10"}]


def test_windows_process_listing_parses_tasklist_csv(monkeypatch) -> None:
    mock_output = "\"python.exe\",\"1234\",\"Console\",\"1\",\"15,000 K\"\n\"cmd.exe\",\"2222\",\"Console\",\"1\",\"3,000 K\"\n"

    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args=args, returncode=0, stdout=mock_output, stderr="")

    monkeypatch.setattr("bw_defend.security.process_control.subprocess.run", mock_run)

    items = _list_processes_windows(limit=2)
    assert items == [
        {"pid": "1234", "command": "python.exe", "etime": "unknown"},
        {"pid": "2222", "command": "cmd.exe", "etime": "unknown"},
    ]
