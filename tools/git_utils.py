"""
Git utilities for pipeline automation.

This module provides utilities for git operations including
repository management, branch operations, and change detection.
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class GitUtils:
    """Utility class for git operations."""

    def __init__(self, repo_path: str = None):
        """Initialize git utilities.

        Args:
            repo_path: Path to git repository (defaults to current directory)
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()

    def run_git_command(self, args: List[str]) -> str:
        """Run a git command and return output.

        Args:
            args: Git command arguments

        Returns:
            Command output as string

        Raises:
            subprocess.CalledProcessError: If git command fails
        """
        cmd = ["git"] + args
        logger.debug(f"Running git command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd, cwd=self.repo_path, capture_output=True, text=True, check=True
        )

        return result.stdout.strip()

    def get_current_branch(self) -> str:
        """Get the current branch name.

        Returns:
            Current branch name
        """
        return self.run_git_command(["branch", "--show-current"])

    def get_remote_url(self, remote: str = "origin") -> str:
        """Get remote repository URL.

        Args:
            remote: Remote name (default: origin)

        Returns:
            Remote URL
        """
        return self.run_git_command(["remote", "get-url", remote])

    def get_changed_files(self, base_ref: str = "HEAD~1") -> List[str]:
        """Get list of changed files since base reference.

        Args:
            base_ref: Base reference to compare against

        Returns:
            List of changed file paths
        """
        output = self.run_git_command(["diff", "--name-only", base_ref])
        if not output:
            return []
        return output.split("\n")

    def get_commit_info(self, ref: str = "HEAD") -> Dict[str, str]:
        """Get commit information.

        Args:
            ref: Git reference (default: HEAD)

        Returns:
            Dictionary with commit information
        """
        format_str = "--format=%H%n%an%n%ae%n%s%n%ci"
        output = self.run_git_command(["show", "--no-patch", format_str, ref])
        lines = output.split("\n")

        return {
            "hash": lines[0],
            "author_name": lines[1],
            "author_email": lines[2],
            "subject": lines[3],
            "date": lines[4],
        }

    def is_clean_working_tree(self) -> bool:
        """Check if working tree is clean.

        Returns:
            True if working tree is clean, False otherwise
        """
        try:
            self.run_git_command(["diff-index", "--quiet", "HEAD"])
            return True
        except subprocess.CalledProcessError:
            return False

    def get_status(self) -> str:
        """Get git status output.

        Returns:
            Git status as string
        """
        return self.run_git_command(["status", "--porcelain"])

    def fetch(self, remote: str = "origin") -> None:
        """Fetch from remote repository.

        Args:
            remote: Remote name to fetch from
        """
        self.run_git_command(["fetch", remote])

    def pull(self, remote: str = "origin", branch: str = None) -> None:
        """Pull changes from remote repository.

        Args:
            remote: Remote name
            branch: Branch name (if None, uses current branch)
        """
        if branch:
            self.run_git_command(["pull", remote, branch])
        else:
            self.run_git_command(["pull", remote])

    def create_branch(self, branch_name: str, start_point: str = "HEAD") -> None:
        """Create a new branch.

        Args:
            branch_name: Name of the new branch
            start_point: Starting point for the branch
        """
        self.run_git_command(["checkout", "-b", branch_name, start_point])

    def checkout(self, ref: str) -> None:
        """Checkout a branch or commit.

        Args:
            ref: Branch name or commit hash to checkout
        """
        self.run_git_command(["checkout", ref])


def get_git_utils(repo_path: str = None) -> GitUtils:
    """Get GitUtils instance.

    Args:
        repo_path: Optional repository path

    Returns:
        GitUtils instance
    """
    return GitUtils(repo_path)
