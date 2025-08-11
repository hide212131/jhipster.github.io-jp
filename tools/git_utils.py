"""Git utilities for translation pipeline."""

import subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path
from config import config


class GitUtils:
    """Git utilities for managing repositories and branches."""
    
    def __init__(self, repo_path: str = "."):
        """Initialize with repository path."""
        self.repo_path = Path(repo_path)
        
    def _run_git_command(self, args: List[str], check: bool = True, capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run a git command and return the result."""
        cmd = ["git"] + args
        return subprocess.run(
            cmd,
            cwd=self.repo_path,
            check=check,
            capture_output=capture_output,
            text=True
        )
    
    def add_upstream_remote(self) -> bool:
        """Add upstream remote if not exists."""
        try:
            # Check if upstream already exists
            result = self._run_git_command(["remote", "get-url", "upstream"], check=False)
            if result.returncode == 0:
                return True  # Already exists
            
            # Add upstream remote
            upstream_url = f"https://github.com/{config.upstream_repo}.git"
            self._run_git_command(["remote", "add", "upstream", upstream_url])
            return True
        except subprocess.CalledProcessError:
            return False
    
    def fetch_upstream(self) -> bool:
        """Fetch from upstream repository."""
        try:
            self._run_git_command(["fetch", "upstream"])
            return True
        except subprocess.CalledProcessError:
            return False
    
    def create_translation_branch(self, branch_name: str) -> bool:
        """Create and checkout translation branch."""
        try:
            # Create and checkout new branch from current HEAD
            self._run_git_command(["checkout", "-b", branch_name])
            return True
        except subprocess.CalledProcessError:
            return False
    
    def get_upstream_changes(self, since_sha: Optional[str] = None) -> List[str]:
        """Get list of changed files from upstream."""
        try:
            if since_sha:
                # Get files changed since specific SHA
                result = self._run_git_command([
                    "diff", "--name-only", f"{since_sha}..upstream/main"
                ])
            else:
                # Get files changed between current HEAD and upstream/main
                result = self._run_git_command([
                    "diff", "--name-only", "HEAD..upstream/main"
                ])
            
            files = result.stdout.strip().split('\n') if result.stdout.strip() else []
            return [f for f in files if f]  # Filter out empty strings
        except subprocess.CalledProcessError:
            return []
    
    def get_file_content(self, file_path: str, ref: str = "HEAD") -> Optional[str]:
        """Get file content from specific ref."""
        try:
            result = self._run_git_command(["show", f"{ref}:{file_path}"])
            return result.stdout
        except subprocess.CalledProcessError:
            return None
    
    def commit_changes(self, message: str, files: List[str] = None) -> bool:
        """Commit changes to current branch."""
        try:
            # Add files (if specified) or all changes
            if files:
                for file in files:
                    self._run_git_command(["add", file])
            else:
                self._run_git_command(["add", "-A"])
            
            # Check if there are any changes to commit
            result = self._run_git_command(["diff", "--cached", "--quiet"], check=False)
            if result.returncode == 0:
                # No changes to commit
                return False
            
            # Commit changes
            self._run_git_command(["commit", "-m", message])
            return True
        except subprocess.CalledProcessError:
            return False
    
    def push_branch(self, branch_name: str, remote: str = "origin") -> bool:
        """Push branch to remote."""
        try:
            self._run_git_command(["push", remote, branch_name])
            return True
        except subprocess.CalledProcessError:
            return False
    
    def get_current_sha(self, ref: str = "HEAD") -> str:
        """Get SHA of current commit."""
        try:
            result = self._run_git_command(["rev-parse", ref])
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return ""
    
    def branch_exists(self, branch_name: str) -> bool:
        """Check if branch exists."""
        try:
            # Check if branch exists locally
            result = self._run_git_command(["show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"], check=False)
            if result.returncode == 0:
                return True
            
            # Check if branch exists remotely
            result = self._run_git_command(["show-ref", "--verify", "--quiet", f"refs/remotes/origin/{branch_name}"], check=False)
            return result.returncode == 0
        except subprocess.CalledProcessError:
            return False

    def create_orphan_branch(self, branch_name: str) -> bool:
        """Create an orphan branch (branch with no commit history)."""
        try:
            self._run_git_command(["checkout", "--orphan", branch_name])
            # Remove all files from staging area
            self._run_git_command(["rm", "-rf", "."], check=False)
            return True
        except subprocess.CalledProcessError:
            return False

    def write_file_to_branch(self, file_path: str, content: str, branch_name: str, commit_message: str) -> bool:
        """Write content to a file in a specific branch."""
        try:
            # Get current branch
            current_branch_result = self._run_git_command(["branch", "--show-current"])
            current_branch = current_branch_result.stdout.strip()
            
            # Switch to target branch
            self._run_git_command(["checkout", branch_name])
            
            # Write content to file
            file_path_obj = self.repo_path / file_path
            file_path_obj.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path_obj, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Add and commit the file
            self._run_git_command(["add", file_path])
            self._run_git_command(["commit", "-m", commit_message])
            
            # Switch back to original branch
            if current_branch:
                self._run_git_command(["checkout", current_branch])
            
            return True
        except subprocess.CalledProcessError:
            return False