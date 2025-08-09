"""
Tests for git utilities module.
"""

import subprocess

# Add tools to path for testing
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

tools_path = Path(__file__).parent.parent / "tools"
sys.path.insert(0, str(tools_path))

from git_utils import GitUtils, get_git_utils


class TestGitUtils:
    """Test cases for GitUtils class."""

    def test_git_utils_initialization(self):
        """Test GitUtils initialization."""
        # Test with default path
        git_utils = GitUtils()
        assert git_utils.repo_path == Path.cwd()

        # Test with custom path
        custom_path = "/tmp/test_repo"
        git_utils = GitUtils(custom_path)
        assert git_utils.repo_path == Path(custom_path)

    @patch("subprocess.run")
    def test_run_git_command_success(self, mock_run):
        """Test successful git command execution."""
        # Setup mock
        mock_result = Mock()
        mock_result.stdout = "command output\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        git_utils = GitUtils()
        result = git_utils.run_git_command(["status"])

        assert result == "command output"
        mock_run.assert_called_once()

        # Check the command was called correctly
        args, kwargs = mock_run.call_args
        assert args[0] == ["git", "status"]
        assert kwargs["cwd"] == git_utils.repo_path
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True
        assert kwargs["check"] is True

    @patch("subprocess.run")
    def test_run_git_command_failure(self, mock_run):
        """Test git command failure handling."""
        # Setup mock to raise CalledProcessError
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        git_utils = GitUtils()

        with pytest.raises(subprocess.CalledProcessError):
            git_utils.run_git_command(["invalid-command"])

    @patch.object(GitUtils, "run_git_command")
    def test_get_current_branch(self, mock_run_git):
        """Test getting current branch."""
        mock_run_git.return_value = "main"

        git_utils = GitUtils()
        branch = git_utils.get_current_branch()

        assert branch == "main"
        mock_run_git.assert_called_once_with(["branch", "--show-current"])

    @patch.object(GitUtils, "run_git_command")
    def test_get_remote_url(self, mock_run_git):
        """Test getting remote URL."""
        mock_run_git.return_value = "https://github.com/user/repo.git"

        git_utils = GitUtils()

        # Test with default remote
        url = git_utils.get_remote_url()
        assert url == "https://github.com/user/repo.git"
        mock_run_git.assert_called_with(["remote", "get-url", "origin"])

        # Test with custom remote
        url = git_utils.get_remote_url("upstream")
        mock_run_git.assert_called_with(["remote", "get-url", "upstream"])

    @patch.object(GitUtils, "run_git_command")
    def test_get_changed_files(self, mock_run_git):
        """Test getting changed files."""
        # Test with changes
        mock_run_git.return_value = "file1.py\nfile2.py\nfile3.md"

        git_utils = GitUtils()
        files = git_utils.get_changed_files()

        assert files == ["file1.py", "file2.py", "file3.md"]
        mock_run_git.assert_called_with(["diff", "--name-only", "HEAD~1"])

        # Test with no changes
        mock_run_git.return_value = ""
        files = git_utils.get_changed_files()
        assert files == []

    @patch.object(GitUtils, "run_git_command")
    def test_get_commit_info(self, mock_run_git):
        """Test getting commit information."""
        commit_output = "abc123def456\nJohn Doe\njohn@example.com\nFix bug in module\n2023-12-01 10:30:00 +0000"
        mock_run_git.return_value = commit_output

        git_utils = GitUtils()
        info = git_utils.get_commit_info()

        expected_info = {
            "hash": "abc123def456",
            "author_name": "John Doe",
            "author_email": "john@example.com",
            "subject": "Fix bug in module",
            "date": "2023-12-01 10:30:00 +0000",
        }

        assert info == expected_info
        mock_run_git.assert_called_with(
            ["show", "--no-patch", "--format=%H%n%an%n%ae%n%s%n%ci", "HEAD"]
        )

    @patch.object(GitUtils, "run_git_command")
    def test_is_clean_working_tree(self, mock_run_git):
        """Test checking if working tree is clean."""
        git_utils = GitUtils()

        # Test clean working tree
        mock_run_git.return_value = ""
        assert git_utils.is_clean_working_tree() is True

        # Test dirty working tree
        mock_run_git.side_effect = subprocess.CalledProcessError(1, "git")
        assert git_utils.is_clean_working_tree() is False

    @patch.object(GitUtils, "run_git_command")
    def test_get_status(self, mock_run_git):
        """Test getting git status."""
        mock_run_git.return_value = " M file1.py\n?? file2.py"

        git_utils = GitUtils()
        status = git_utils.get_status()

        assert status == " M file1.py\n?? file2.py"
        mock_run_git.assert_called_with(["status", "--porcelain"])

    @patch.object(GitUtils, "run_git_command")
    def test_fetch(self, mock_run_git):
        """Test fetching from remote."""
        git_utils = GitUtils()
        git_utils.fetch()

        mock_run_git.assert_called_with(["fetch", "origin"])

        # Test with custom remote
        git_utils.fetch("upstream")
        mock_run_git.assert_called_with(["fetch", "upstream"])

    @patch.object(GitUtils, "run_git_command")
    def test_pull(self, mock_run_git):
        """Test pulling from remote."""
        git_utils = GitUtils()

        # Test without specifying branch
        git_utils.pull()
        mock_run_git.assert_called_with(["pull", "origin"])

        # Test with specific branch
        git_utils.pull("origin", "main")
        mock_run_git.assert_called_with(["pull", "origin", "main"])

    @patch.object(GitUtils, "run_git_command")
    def test_create_branch(self, mock_run_git):
        """Test creating a new branch."""
        git_utils = GitUtils()
        git_utils.create_branch("feature-branch")

        mock_run_git.assert_called_with(["checkout", "-b", "feature-branch", "HEAD"])

        # Test with custom start point
        git_utils.create_branch("feature-branch", "main")
        mock_run_git.assert_called_with(["checkout", "-b", "feature-branch", "main"])

    @patch.object(GitUtils, "run_git_command")
    def test_checkout(self, mock_run_git):
        """Test checking out a branch or commit."""
        git_utils = GitUtils()
        git_utils.checkout("main")

        mock_run_git.assert_called_with(["checkout", "main"])


def test_get_git_utils():
    """Test the get_git_utils factory function."""
    # Test with default path
    git_utils = get_git_utils()
    assert isinstance(git_utils, GitUtils)
    assert git_utils.repo_path == Path.cwd()

    # Test with custom path
    custom_path = "/tmp/test"
    git_utils = get_git_utils(custom_path)
    assert git_utils.repo_path == Path(custom_path)
