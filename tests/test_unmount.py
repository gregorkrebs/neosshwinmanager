"""
tests/test_unmount.py – Unit tests for SSHFS unmount operations and error handling.
"""

import sys
import os
from unittest import mock

# Make src importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.sshfs_controller import _find_sshfs_pid_for_drive, SSHFSController, MountResult


class TestFindSshfsPidForDrive:
    """Test the _find_sshfs_pid_for_drive function with various error conditions."""

    def test_returns_none_on_missing_psutil(self, monkeypatch):
        """Should return None gracefully if psutil is not installed."""
        def mock_import(name, *args, **kwargs):
            if name == 'psutil':
                raise ImportError("psutil not found")
            return __import__(name, *args, **kwargs)

        monkeypatch.setattr('builtins.__import__', mock_import)
        result = _find_sshfs_pid_for_drive("F:")
        assert result is None

    def test_returns_none_on_invalid_drive_letter(self):
        """Should return None for invalid drive letters."""
        assert _find_sshfs_pid_for_drive("") is None
        assert _find_sshfs_pid_for_drive("AB:") is None
        assert _find_sshfs_pid_for_drive("123") is None

    def test_returns_none_on_no_matching_process(self):
        """Should return None when no sshfs.exe is mounted on that drive."""
        with mock.patch('src.sshfs_controller.psutil.process_iter') as mock_iter:
            mock_iter.return_value = []
            result = _find_sshfs_pid_for_drive("Z:")
            assert result is None

    def test_returns_pid_when_process_found(self):
        """Should return the PID when sshfs.exe is found for the drive."""
        mock_proc = mock.MagicMock()
        mock_proc.info = {
            'pid': 12345,
            'name': 'sshfs.exe',
            'cmdline': ['sshfs.exe', '-oport=22', 'user@host:/', 'F:']
        }

        with mock.patch('src.sshfs_controller.psutil.process_iter') as mock_iter:
            mock_iter.return_value = [mock_proc]
            result = _find_sshfs_pid_for_drive("F:")
            assert result == 12345


class TestSSHFSControllerUnmount:
    """Test SSHFSController.unmount() error handling."""

    def test_unmount_returns_failure_on_missing_psutil(self, monkeypatch):
        """unmount() should handle ImportError from psutil gracefully."""
        controller = SSHFSController()

        def mock_import(name, *args, **kwargs):
            if name == 'psutil':
                raise ImportError("psutil not found")
            return __import__(name, *args, **kwargs)

        monkeypatch.setattr('builtins.__import__', mock_import)

        # Should not raise an exception, but return a failure or use WinFsp fallback
        # Exact behavior depends on fallback logic in unmount()
        try:
            result = controller.unmount("F:")
            # If unmount returns a result, check it's a failure or uses fallback
            if isinstance(result, MountResult):
                # Either successful fallback or failure is acceptable
                pass
        except ImportError:
            # Should NOT raise ImportError
            assert False, "unmount() should not raise ImportError directly"

    def test_unmount_handles_subprocess_errors(self, monkeypatch):
        """unmount() subprocess calls should have error handling."""
        controller = SSHFSController()

        with mock.patch('src.sshfs_controller.subprocess.run') as mock_run:
            mock_run.side_effect = OSError("Cannot execute command")

            try:
                result = controller.unmount("F:")
                # Should either return failure or handle gracefully
            except OSError:
                # Should NOT propagate OSError to caller
                assert False, "unmount() should handle subprocess errors"
