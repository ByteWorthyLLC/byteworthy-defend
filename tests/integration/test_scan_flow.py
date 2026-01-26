"""
Integration tests for end-to-end scan workflow.
"""

import pytest

from hifzdefend.core.engine import ScanEngine


@pytest.mark.integration
@pytest.mark.requires_clamav
class TestScanWorkflow:
    """Integration tests for complete scan workflow."""

    def test_scan_clean_file(self, scan_engine, clean_file):
        """Test scanning a clean file end-to-end."""
        report = scan_engine.scan_path(clean_file)

        assert report.files_scanned == 1
        assert report.threats_count == 0
        assert not report.has_threats
        assert len(report.errors) == 0

    def test_scan_eicar(self, scan_engine, eicar_file):
        """Test detecting EICAR test file."""
        # Disable auto-quarantine for this test
        scan_engine.config.quarantine.auto_quarantine = False

        report = scan_engine.scan_path(eicar_file)

        assert report.files_scanned == 1
        assert report.threats_count == 1
        assert report.has_threats
        assert len(report.threats_found) == 1

        threat = report.threats_found[0]
        assert "EICAR" in threat["threat_name"] or "Eicar" in threat["threat_name"]
        assert threat["file_path"] == str(eicar_file)

    def test_scan_directory(self, scan_engine, temp_dir, clean_file):
        """Test scanning a directory."""
        # Create multiple files
        (temp_dir / "file1.txt").write_text("Clean file 1")
        (temp_dir / "file2.txt").write_text("Clean file 2")

        report = scan_engine.scan_path(temp_dir)

        assert report.files_scanned >= 2
        assert report.threats_count == 0

    def test_quarantine_workflow(self, scan_engine, eicar_file):
        """Test quarantine workflow."""
        # Enable auto-quarantine
        scan_engine.config.quarantine.auto_quarantine = True

        # Scan EICAR (should auto-quarantine)
        report = scan_engine.scan_path(eicar_file)

        assert report.threats_count == 1
        threat = report.threats_found[0]
        assert threat["quarantined"] is True

        # Original file should be moved
        assert not eicar_file.exists()

        # Quarantine directory should have the file
        quarantine_dir = scan_engine.config.quarantine.quarantine_dir_path
        quarantined_files = list(quarantine_dir.glob("*.quarantined"))
        assert len(quarantined_files) >= 1

    def test_excluded_extensions(self, scan_engine, temp_dir):
        """Test that excluded extensions are skipped."""
        # Configure to exclude .log files
        scan_engine.config.scanning.excluded_extensions = [".log"]

        # Create files
        txt_file = temp_dir / "test.txt"
        log_file = temp_dir / "test.log"

        txt_file.write_text("Clean text file")
        log_file.write_text("Log file content")

        # Scan directory
        report = scan_engine.scan_path(temp_dir)

        # Only txt file should be scanned
        assert txt_file.name in [Path(f).name for f in report.scanned_files]
        assert log_file.name not in [Path(f).name for f in report.scanned_files]

    def test_max_file_size(self, scan_engine, temp_dir):
        """Test that files exceeding max size are skipped."""
        # Set small max file size
        scan_engine.config.scanning.max_file_size = 100  # 100 bytes

        # Create small and large files
        small_file = temp_dir / "small.txt"
        large_file = temp_dir / "large.txt"

        small_file.write_text("Small")
        large_file.write_text("X" * 200)  # 200 bytes

        # Scan directory
        report = scan_engine.scan_path(temp_dir)

        # Only small file should be scanned
        scanned_names = [Path(f).name for f in report.scanned_files]
        assert small_file.name in scanned_names
        assert large_file.name not in scanned_names
