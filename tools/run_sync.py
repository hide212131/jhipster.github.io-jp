"""Main synchronization runner for LLM translation pipeline."""

import click
import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from git_utils import GitUtils
from config import config
from discover_changes import ChangeDiscoverer
from apply_changes import ChangeApplicator
from pr_body import PRBodyGenerator
from verify_alignment import AlignmentVerifier


class SyncRunner:
    """Main synchronization runner."""
    
    def __init__(self):
        """Initialize sync runner."""
        self.git_utils = GitUtils()
        self.discoverer = ChangeDiscoverer()
        self.applicator = ChangeApplicator()
        self.pr_generator = PRBodyGenerator()
        self.verifier = AlignmentVerifier()
    
    def run_ci_mode(self, branch_prefix: str = "translate/sync", **kwargs) -> Dict[str, Any]:
        """Run in CI mode - full sync with PR creation."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        branch_name = f"{branch_prefix}-{timestamp}"
        
        results = {
            "mode": "ci",
            "branch_name": branch_name,
            "timestamp": timestamp,
            "pr_needed": False,
            "steps": []
        }
        
        try:
            # Step 1: Setup upstream and fetch
            self._log_step(results, "setup", "Setting up upstream and fetching changes")
            if not self.git_utils.add_upstream_remote():
                raise Exception("Failed to add upstream remote")
            if not self.git_utils.fetch_upstream():
                raise Exception("Failed to fetch upstream")
            
            # Step 2: Discover changes
            self._log_step(results, "discover", "Discovering changes from upstream")
            changes = self.discoverer.discover_changes()
            
            # Check if there are any changes that need processing
            has_changes = any(
                len(files) > 0 for files in changes["files"].values() 
                if files and any(f.get("status") != "unchanged" for f in files)
            )
            
            if not has_changes:
                self._log_step(results, "no_changes", "No changes found, skipping PR creation")
                return results
            
            # Step 3: Create translation branch
            self._log_step(results, "branch", f"Creating translation branch: {branch_name}")
            if not self.git_utils.create_translation_branch(branch_name):
                raise Exception(f"Failed to create branch {branch_name}")
            
            # Step 4: Apply changes
            self._log_step(results, "apply", "Applying translation changes")
            changes_file = str(config.output_dir / "changes.json")
            with open(changes_file, 'w', encoding='utf-8') as f:
                json.dump(changes, f, indent=2, ensure_ascii=False)
            
            apply_results = self.applicator.apply_changes(changes_file)
            
            # Step 5: Verify changes
            self._log_step(results, "verify", "Verifying alignment and structure")
            # TODO: Add verification step
            
            # Step 6: Commit changes
            self._log_step(results, "commit", "Committing translation changes")
            commit_message = f"feat: sync translations from upstream ({timestamp})"
            if self.git_utils.commit_changes(commit_message):
                results["pr_needed"] = True
            
            # Step 7: Generate PR body
            if results["pr_needed"]:
                self._log_step(results, "pr_body", "Generating PR body")
                apply_results_file = str(config.output_dir / "apply_results.json")
                with open(apply_results_file, 'w', encoding='utf-8') as f:
                    json.dump(apply_results, f, indent=2, ensure_ascii=False)
                
                pr_body = self.pr_generator.generate_pr_body(changes_file, apply_results_file)
                pr_body_file = str(config.output_dir / "pr_body.md")
                with open(pr_body_file, 'w', encoding='utf-8') as f:
                    f.write(pr_body)
                
                # Set environment variable for GitHub Actions
                if os.getenv("GITHUB_ENV"):
                    with open(os.getenv("GITHUB_ENV"), "a") as f:
                        f.write("PR_NEEDED=1\n")
            
            self._log_step(results, "complete", "Synchronization completed successfully")
            
        except Exception as e:
            self._log_step(results, "error", f"Error: {e}")
            results["error"] = str(e)
        
        return results
    
    def run_dev_mode(self, before_sha: Optional[str] = None, limit: Optional[int] = None, 
                     paths: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Run in development mode - limited sync for testing."""
        results = {
            "mode": "dev",
            "before_sha": before_sha,
            "limit": limit,
            "paths": paths,
            "steps": []
        }
        
        try:
            # Step 1: Setup upstream
            self._log_step(results, "setup", "Setting up upstream (dev mode)")
            if not self.git_utils.add_upstream_remote():
                print("Warning: Could not add upstream remote")
            if not self.git_utils.fetch_upstream():
                print("Warning: Could not fetch upstream")
            
            # Step 2: Discover changes with filters
            self._log_step(results, "discover", f"Discovering changes (limit: {limit}, before: {before_sha})")
            changes = self.discoverer.discover_changes()
            
            # Apply filters for dev mode
            if before_sha:
                # TODO: Filter changes to only include those before specific SHA
                pass
            
            if paths:
                # Filter by path patterns
                path_patterns = paths.split(',')
                filtered_changes = {"files": {}}
                for category, files in changes["files"].items():
                    filtered_files = []
                    for file_info in files:
                        file_path = file_info["path"]
                        if any(pattern in file_path for pattern in path_patterns):
                            filtered_files.append(file_info)
                    filtered_changes["files"][category] = filtered_files
                changes = filtered_changes
            
            if limit:
                # Limit number of files to process
                for category in changes["files"]:
                    changes["files"][category] = changes["files"][category][:limit]
            
            # Step 3: Apply changes (without branch creation)
            self._log_step(results, "apply", "Applying changes (dev mode)")
            changes_file = str(config.output_dir / "dev_changes.json")
            with open(changes_file, 'w', encoding='utf-8') as f:
                json.dump(changes, f, indent=2, ensure_ascii=False)
            
            apply_results = self.applicator.apply_changes(changes_file)
            
            # Step 4: Show results
            self._log_step(results, "complete", "Development sync completed")
            results["apply_results"] = apply_results
            
        except Exception as e:
            self._log_step(results, "error", f"Error: {e}")
            results["error"] = str(e)
        
        return results
    
    def _log_step(self, results: Dict[str, Any], step_name: str, message: str):
        """Log a step in the process."""
        step = {
            "name": step_name,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        results["steps"].append(step)
        print(f"[{step_name.upper()}] {message}")


@click.command()
@click.option('--mode', type=click.Choice(['ci', 'dev']), required=True, help='Run mode: ci (full sync) or dev (development)')
@click.option('--branch', default='translate/sync', help='Branch prefix for CI mode')
@click.option('--before', 'before_sha', help='Process only changes before this upstream SHA (dev mode)')
@click.option('--limit', type=int, help='Limit number of files to process (dev mode)')
@click.option('--paths', help='Comma-separated path patterns to filter (dev mode)')
@click.option('--output', '-o', help='Output file for results (default: .out/sync_results.json)')
@click.help_option('--help', '-h')
def main(mode: str, branch: str, before_sha: str, limit: int, paths: str, output: str):
    """Main synchronization runner for LLM translation pipeline.
    
    This is the primary tool that orchestrates the entire translation sync process.
    It can run in CI mode for full automated sync or dev mode for testing.
    
    CI Mode Examples:
        python run_sync.py --mode ci
        python run_sync.py --mode ci --branch translate/feature-sync
    
    Dev Mode Examples:
        python run_sync.py --mode dev --limit 3
        python run_sync.py --mode dev --before abcd1234 --paths "docs/getting-started"
        python run_sync.py --mode dev --limit 1 --paths "docs/**"
    """
    
    try:
        # Validate configuration
        if not config.validate():
            if mode == 'ci':
                click.echo("Error: Configuration validation failed (missing API keys)", err=True)
                return 1
            else:
                click.echo("Warning: Some configuration missing, continuing in dev mode")
        
        if not output:
            output = str(config.output_dir / "sync_results.json")
        
        click.echo(f"Starting sync in {mode} mode...")
        
        # Run sync
        runner = SyncRunner()
        
        if mode == 'ci':
            results = runner.run_ci_mode(
                branch_prefix=branch,
                before_sha=before_sha,
                limit=limit,
                paths=paths
            )
        else:  # dev mode
            results = runner.run_dev_mode(
                before_sha=before_sha,
                limit=limit,
                paths=paths
            )
        
        # Save results
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Print summary
        click.echo(f"\n=== Sync Results ===")
        click.echo(f"Mode: {results['mode']}")
        click.echo(f"Steps completed: {len(results['steps'])}")
        
        if results.get("error"):
            click.echo(f"Error: {results['error']}")
            return 1
        
        if mode == 'ci':
            click.echo(f"Branch: {results.get('branch_name', 'N/A')}")
            click.echo(f"PR needed: {results.get('pr_needed', False)}")
        elif mode == 'dev':
            apply_results = results.get("apply_results", {})
            stats = apply_results.get("statistics", {})
            click.echo(f"Files processed: {stats.get('translated', 0) + stats.get('copied', 0)}")
            click.echo(f"Errors: {len(apply_results.get('errors', []))}")
        
        click.echo(f"Results saved to: {output}")
        
        return 0
        
    except Exception as e:
        click.echo(f"Error running sync: {e}", err=True)
        return 1


if __name__ == '__main__':
    exit(main())