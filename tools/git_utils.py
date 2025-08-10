#!/usr/bin/env python3
"""
Git utilities for JHipster translation tools.
Provides helper functions for Git operations.
"""

import subprocess
from typing import List, Optional
from pathlib import Path


class GitUtils:
    """Git utility functions."""
    
    def __init__(self, repo_path: str = "."):
        """Initialize with repository path."""
        self.repo_path = Path(repo_path)
    
    def run_git_command(self, args: List[str]) -> str:
        """Run a git command and return output."""
        cmd = ["git"] + args
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git command failed: {' '.join(cmd)}\n{e.stderr}")
    
    def get_current_branch(self) -> str:
        """Get current branch name."""
        return self.run_git_command(["branch", "--show-current"])
    
    def get_changed_files(self, base_branch: str = "main") -> List[str]:
        """Get list of changed files compared to base branch."""
        output = self.run_git_command(["diff", "--name-only", base_branch])
        return [f for f in output.split('\n') if f.strip()]
    
    def get_file_content(self, file_path: str, commit: str = "HEAD") -> str:
        """Get content of a file at specific commit."""
        return self.run_git_command(["show", f"{commit}:{file_path}"])
    
    def is_git_repo(self) -> bool:
        """Check if current directory is a git repository."""
        try:
            self.run_git_command(["rev-parse", "--git-dir"])
            return True
        except RuntimeError:
            return False