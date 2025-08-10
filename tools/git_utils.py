"""Git utilities for managing repository operations."""

import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import git


class GitUtils:
    """Utilities for Git operations."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.repo = git.Repo(repo_path)

    def add_upstream_remote(self, upstream_url: str) -> bool:
        """Add upstream remote if it doesn't exist."""
        try:
            self.repo.create_remote("upstream", upstream_url)
            return True
        except git.exc.GitCommandError:
            # Remote already exists
            return False

    def fetch_upstream(self) -> bool:
        """Fetch from upstream remote."""
        try:
            upstream = self.repo.remotes.upstream
            upstream.fetch()
            return True
        except Exception as e:
            print(f"Error fetching upstream: {e}")
            return False

    def get_commits_between(self, base_ref: str, head_ref: str) -> List[Dict[str, Any]]:
        """Get list of commits between two references."""
        commits = []
        try:
            for commit in self.repo.iter_commits(f"{base_ref}..{head_ref}"):
                commits.append(
                    {
                        "sha": commit.hexsha,
                        "message": commit.message.strip(),
                        "author": str(commit.author),
                        "date": commit.committed_datetime.isoformat(),
                        "files": [item.a_path for item in commit.stats.files.keys()],
                    }
                )
        except Exception as e:
            print(f"Error getting commits: {e}")
        return commits

    def get_file_content(self, file_path: str, ref: str = "HEAD") -> Optional[str]:
        """Get file content at specific reference."""
        try:
            blob = self.repo.commit(ref).tree / file_path
            return blob.data_stream.read().decode("utf-8")
        except Exception as e:
            print(f"Error reading file {file_path} at {ref}: {e}")
            return None

    def create_branch(self, branch_name: str, base_ref: str = "HEAD") -> bool:
        """Create a new branch."""
        try:
            self.repo.create_head(branch_name, base_ref)
            return True
        except Exception as e:
            print(f"Error creating branch {branch_name}: {e}")
            return False

    def checkout_branch(self, branch_name: str) -> bool:
        """Checkout a branch."""
        try:
            self.repo.heads[branch_name].checkout()
            return True
        except Exception as e:
            print(f"Error checking out branch {branch_name}: {e}")
            return False

    def commit_changes(self, message: str, files: List[str] = None) -> bool:
        """Commit changes to repository."""
        try:
            if files:
                self.repo.index.add(files)
            else:
                self.repo.git.add(A=True)
            self.repo.index.commit(message)
            return True
        except Exception as e:
            print(f"Error committing changes: {e}")
            return False
