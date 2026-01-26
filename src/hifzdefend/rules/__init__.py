"""Custom Rules Engine for HifzDefend.

This module provides:
- YARA rule compilation and execution
- Custom threat signatures
- File type blocking with context awareness
- Application whitelisting with hash verification
- Composite rule conditions
- Automated response actions
"""

from hifzdefend.rules.engine import RulesEngine
from hifzdefend.rules.yara_manager import YARAManager, YARAMatch
from hifzdefend.rules.file_blocker import FileBlocker, BlockReason
from hifzdefend.rules.app_whitelist import ApplicationWhitelist, WhitelistEntry

__all__ = [
    "RulesEngine",
    "YARAManager",
    "YARAMatch",
    "FileBlocker",
    "BlockReason",
    "ApplicationWhitelist",
    "WhitelistEntry",
]
