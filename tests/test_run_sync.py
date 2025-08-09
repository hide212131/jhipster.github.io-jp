"""
Tests for run_sync script.
"""

import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add tools to path for testing
tools_path = Path(__file__).parent.parent / "tools"
sys.path.insert(0, str(tools_path))

import run_sync


class TestRunSync:
    """Test cases for run_sync module."""

    def test_setup_logging(self):
        """Test logging setup."""
        # Test basic setup - should not raise any errors
        run_sync.setup_logging("INFO")
        run_sync.setup_logging("DEBUG")
        run_sync.setup_logging("ERROR")

    @patch("run_sync.get_git_utils")
    @patch("logging.getLogger")
    def test_sync_repository_dry_run(self, mock_logger, mock_get_git_utils):
        """Test repository sync in dry run mode."""
        # Setup mocks
        mock_git_utils = Mock()
        mock_git_utils.get_current_branch.return_value = "main"
        mock_git_utils.is_clean_working_tree.return_value = True
        mock_get_git_utils.return_value = mock_git_utils

        mock_log = Mock()
        mock_logger.return_value = mock_log

        # Test dry run
        run_sync.sync_repository("source", "target", dry_run=True)

        # Verify git utils were called
        mock_git_utils.get_current_branch.assert_called_once()
        mock_git_utils.is_clean_working_tree.assert_called_once()
        mock_git_utils.fetch.assert_called_once()

        # Verify logging
        assert mock_log.info.call_count >= 3  # Should have multiple info logs

    @patch("run_sync.get_git_utils")
    @patch("logging.getLogger")
    def test_sync_repository_dirty_tree(self, mock_logger, mock_get_git_utils):
        """Test repository sync with dirty working tree."""
        # Setup mocks
        mock_git_utils = Mock()
        mock_git_utils.get_current_branch.return_value = "main"
        mock_git_utils.is_clean_working_tree.return_value = False
        mock_git_utils.get_status.return_value = " M file1.py"
        mock_get_git_utils.return_value = mock_git_utils

        mock_log = Mock()
        mock_logger.return_value = mock_log

        # Test with dirty tree
        run_sync.sync_repository("source", "target", dry_run=False)

        # Verify status was checked
        mock_git_utils.get_status.assert_called_once()

        # Verify warning was logged
        mock_log.warning.assert_called_once_with("Working tree is not clean")

    @patch("run_sync.get_git_utils")
    @patch("logging.getLogger")
    def test_sync_repository_error(self, mock_logger, mock_get_git_utils):
        """Test repository sync error handling."""
        # Setup mocks to raise an exception
        mock_git_utils = Mock()
        mock_git_utils.get_current_branch.side_effect = Exception("Git error")
        mock_get_git_utils.return_value = mock_git_utils

        mock_log = Mock()
        mock_logger.return_value = mock_log

        # Test error handling
        with pytest.raises(Exception, match="Git error"):
            run_sync.sync_repository("source", "target")

        # Verify error was logged
        mock_log.error.assert_called_once()

    @patch("sys.argv", ["run_sync.py", "--help"])
    def test_main_help_argument(self):
        """Test main function with help argument."""
        with pytest.raises(SystemExit) as exc_info:
            run_sync.main()

        # Help should exit with code 0
        assert exc_info.value.code == 0

    @patch("sys.argv", ["run_sync.py", "--version"])
    def test_main_version_argument(self):
        """Test main function with version argument."""
        with pytest.raises(SystemExit) as exc_info:
            run_sync.main()

        # Version should exit with code 0
        assert exc_info.value.code == 0

    @patch("run_sync.sync_repository")
    @patch(
        "sys.argv",
        ["run_sync.py", "sync", "--source", "origin/main", "--target", "local"],
    )
    def test_main_sync_action(self, mock_sync):
        """Test main function with sync action."""
        run_sync.main()

        # Verify sync was called with correct arguments
        mock_sync.assert_called_once_with("origin/main", "local", False)

    @patch("run_sync.sync_repository")
    @patch("sys.argv", ["run_sync.py", "sync", "--dry-run"])
    def test_main_sync_dry_run(self, mock_sync):
        """Test main function with dry run option."""
        run_sync.main()

        # Verify sync was called with dry_run=True
        mock_sync.assert_called_once_with("origin/main", "local", True)

    @patch("run_sync.get_git_utils")
    @patch("sys.argv", ["run_sync.py", "status"])
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_status_action(self, mock_stdout, mock_get_git_utils):
        """Test main function with status action."""
        # Setup mock
        mock_git_utils = Mock()
        mock_git_utils.get_current_branch.return_value = "main"
        mock_git_utils.get_status.return_value = ""
        mock_get_git_utils.return_value = mock_git_utils

        run_sync.main()

        # Verify output
        output = mock_stdout.getvalue()
        assert "Current branch: main" in output
        assert "Working tree is clean" in output

    @patch("run_sync.get_git_utils")
    @patch("sys.argv", ["run_sync.py", "status"])
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_status_action_with_changes(self, mock_stdout, mock_get_git_utils):
        """Test main function with status action and changes."""
        # Setup mock
        mock_git_utils = Mock()
        mock_git_utils.get_current_branch.return_value = "feature"
        mock_git_utils.get_status.return_value = " M file1.py\n?? file2.py"
        mock_get_git_utils.return_value = mock_git_utils

        run_sync.main()

        # Verify output
        output = mock_stdout.getvalue()
        assert "Current branch: feature" in output
        assert "Modified files:" in output
        assert " M file1.py" in output

    @patch("run_sync.get_git_utils")
    @patch("sys.argv", ["run_sync.py", "check"])
    def test_main_check_action_success(self, mock_get_git_utils):
        """Test main function with check action (success)."""
        # Setup mock
        mock_git_utils = Mock()
        mock_git_utils.get_remote_url.return_value = "https://github.com/user/repo.git"
        mock_get_git_utils.return_value = mock_git_utils

        # Should not raise any exception
        run_sync.main()

    @patch("run_sync.get_git_utils")
    @patch("sys.argv", ["run_sync.py", "check"])
    def test_main_check_action_failure(self, mock_get_git_utils):
        """Test main function with check action (failure)."""
        # Setup mock to raise exception
        mock_git_utils = Mock()
        mock_git_utils.get_remote_url.side_effect = Exception("No remote found")
        mock_get_git_utils.return_value = mock_git_utils

        # Should exit with code 1
        with pytest.raises(SystemExit) as exc_info:
            run_sync.main()

        assert exc_info.value.code == 1

    @patch("run_sync.sync_repository")
    @patch("sys.argv", ["run_sync.py", "sync"])
    def test_main_keyboard_interrupt(self, mock_sync):
        """Test main function handling KeyboardInterrupt."""
        # Setup mock to raise KeyboardInterrupt
        mock_sync.side_effect = KeyboardInterrupt()

        # Should exit with code 130
        with pytest.raises(SystemExit) as exc_info:
            run_sync.main()

        assert exc_info.value.code == 130

    @patch("run_sync.sync_repository")
    @patch("sys.argv", ["run_sync.py", "sync"])
    def test_main_general_exception(self, mock_sync):
        """Test main function handling general exceptions."""
        # Setup mock to raise exception
        mock_sync.side_effect = Exception("General error")

        # Should exit with code 1
        with pytest.raises(SystemExit) as exc_info:
            run_sync.main()

        assert exc_info.value.code == 1

    @patch("run_sync.sync_repository")
    @patch("sys.argv", ["run_sync.py", "--verbose"])
    @patch("run_sync.setup_logging")
    def test_main_verbose_logging(self, mock_setup_logging, mock_sync):
        """Test main function with verbose logging."""
        run_sync.main()

        # Verify DEBUG logging was set
        mock_setup_logging.assert_called_with("DEBUG")
        # Verify sync was called (default action)
        mock_sync.assert_called_once()

    @patch("run_sync.sync_repository")
    @patch("sys.argv", ["run_sync.py", "--quiet"])
    @patch("run_sync.setup_logging")
    def test_main_quiet_logging(self, mock_setup_logging, mock_sync):
        """Test main function with quiet logging."""
        run_sync.main()

        # Verify ERROR logging was set
        mock_setup_logging.assert_called_with("ERROR")
        # Verify sync was called (default action)
        mock_sync.assert_called_once()
