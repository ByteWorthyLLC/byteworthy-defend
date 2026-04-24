import pytest

from bw_defend.core.engine import scan_target
from bw_defend.core.errors import ScanTargetError


def test_scan_target_missing_path_raises() -> None:
    with pytest.raises(ScanTargetError):
        scan_target("/tmp/path/that/does/not/exist-12345")
