"""Git utilities for JHipster.github.io-jp tools."""

import os
import subprocess
from typing import List, Optional, Tuple


class GitUtils:
    """Utility class for Git operations."""

    def __init__(self, repo_path: Optional[str] = None):
        """Initialize with repository path."""
        self.repo_path = repo_path or os.getcwd()

    def run_git_command(self, args: List[str]) -> Tuple[bool, str, str]:
        """Run git command and return success, stdout, stderr."""
        cmd = ["git"] + args
        try:
            result = subprocess.run(
                cmd, cwd=self.repo_path, capture_output=True, text=True, check=False
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return False, "", str(e)

    def get_current_branch(self) -> Optional[str]:
        """Get current git branch name."""
        success, stdout, _ = self.run_git_command(["branch", "--show-current"])
        return stdout if success else None

    def get_changed_files(self, base_branch: str = "main") -> List[str]:
        """Get list of files changed compared to base branch."""
        success, stdout, _ = self.run_git_command(
            ["diff", "--name-only", f"{base_branch}...HEAD"]
        )
        return stdout.split("\n") if success and stdout else []

    def is_repository(self) -> bool:
        """Check if current directory is a git repository."""
        success, _, _ = self.run_git_command(["rev-parse", "--git-dir"])
        return success

    def get_repository_root(self) -> Optional[str]:
        """Get repository root directory."""
        success, stdout, _ = self.run_git_command(["rev-parse", "--show-toplevel"])
        return stdout if success else None

    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes."""
        success, stdout, _ = self.run_git_command(["status", "--porcelain"])
        return success and bool(stdout.strip())


# Global git utils instance
git_utils = GitUtils()
