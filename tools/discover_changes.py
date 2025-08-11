"""Discover changes between upstream and current repository."""

import click
import json
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime
from git_utils import GitUtils
from file_filters import FileFilter
from line_diff import LineDiff
from manifest_manager import ManifestManager
from config import config


class ChangeDiscoverer:
    """Discover changes between upstream and current state."""
    
    def __init__(self):
        """Initialize change discoverer."""
        self.git_utils = GitUtils()
        self.file_filter = FileFilter()
        self.line_diff = LineDiff()
        self.manifest_manager = ManifestManager(self.git_utils)
    
    def discover_changes(self, upstream_ref: str = "upstream/main", meta_branch: str = "translation-meta", before_sha: str = None) -> Dict[str, Any]:
        """Discover changes between upstream and current state."""
        changes = {
            "upstream_ref": upstream_ref,
            "meta_branch": meta_branch,
            "before_sha": before_sha,
            "timestamp": datetime.now().isoformat(),
            "files": {}
        }
        
        # Get list of changed files from upstream, optionally limited by before_sha
        changed_files = self.git_utils.get_upstream_changes(since_sha=before_sha)
        
        # Filter files by type
        filtered_files = self.file_filter.filter_files(changed_files)
        
        # Process each file category
        for category, files in filtered_files.items():
            changes["files"][category] = []
            
            for file_path in files:
                file_change = self._analyze_file_change(file_path, upstream_ref)
                if file_change:
                    changes["files"][category].append(file_change)
        
        return changes
    
    def _analyze_file_change(self, file_path: str, upstream_ref: str) -> Dict[str, Any]:
        """Analyze change for a specific file."""
        try:
            # Get current upstream SHA for comparison
            current_upstream_sha = self.git_utils.get_current_sha(upstream_ref)
            
            # Get manifest info for this file
            manifest_upstream_sha = self.manifest_manager.get_file_upstream_sha(file_path)
            previous_strategy = self.manifest_manager.get_file_strategy(file_path)
            
            # Get upstream content
            upstream_content = self.git_utils.get_file_content(file_path, upstream_ref)
            
            # Get content from manifest SHA if it exists, otherwise compare against current local
            if manifest_upstream_sha:
                baseline_content = self.git_utils.get_file_content(file_path, manifest_upstream_sha)
            else:
                # No manifest entry, compare against current local content
                baseline_content = self.git_utils.get_file_content(file_path, "HEAD")
            
            if upstream_content is None and baseline_content is not None:
                return {
                    "path": file_path,
                    "status": "deleted",
                    "operations": [],
                    "summary": {"total_operations": 0},
                    "manifest_sha": manifest_upstream_sha,
                    "current_upstream_sha": current_upstream_sha,
                    "previous_strategy": previous_strategy,
                    "needs_update": manifest_upstream_sha != current_upstream_sha
                }
            
            if upstream_content is not None and baseline_content is None:
                return {
                    "path": file_path,
                    "status": "added",
                    "operations": [],
                    "summary": {"total_operations": 0},
                    "manifest_sha": manifest_upstream_sha,
                    "current_upstream_sha": current_upstream_sha,
                    "previous_strategy": previous_strategy,
                    "needs_update": manifest_upstream_sha != current_upstream_sha
                }
            
            # Compare baseline with current upstream
            baseline_lines = baseline_content.split('\n') if baseline_content else []
            upstream_lines = upstream_content.split('\n') if upstream_content else []
            
            operations = self.line_diff.get_diff_operations(baseline_lines, upstream_lines)
            summary = self.line_diff.get_diff_summary(operations)
            
            # Convert operations to serializable format
            serializable_ops = []
            for op in operations:
                serializable_ops.append({
                    "operation": op.operation,
                    "old_start": op.old_start,
                    "old_end": op.old_end,
                    "new_start": op.new_start,
                    "new_end": op.new_end,
                    "old_lines": op.old_lines,
                    "new_lines": op.new_lines,
                    "similarity_ratio": op.similarity_ratio,
                    "change_type": self.line_diff.classify_change_type(op),
                    "strategy": self.line_diff.get_translation_strategy(op)
                })
            
            return {
                "path": file_path,
                "status": "modified" if operations else "unchanged",
                "operations": serializable_ops,
                "summary": summary,
                "manifest_sha": manifest_upstream_sha,
                "current_upstream_sha": current_upstream_sha,
                "previous_strategy": previous_strategy,
                "needs_update": manifest_upstream_sha != current_upstream_sha
            }
            
        except Exception as e:
            return {
                "path": file_path,
                "status": "error",
                "error": str(e),
                "operations": [],
                "summary": {"total_operations": 0},
                "manifest_sha": None,
                "current_upstream_sha": None,
                "previous_strategy": None,
                "needs_update": False
            }


@click.command()
@click.option('--upstream-ref', default='upstream/main', help='Upstream reference to compare against')
@click.option('--meta-branch', default='translation-meta', help='Meta branch for tracking translation state')
@click.option('--output', '-o', help='Output file for changes JSON (default: .out/changes.json)')
@click.option('--format', 'output_format', type=click.Choice(['json', 'summary']), default='json', help='Output format')
@click.option('--filter-type', type=click.Choice(['all', 'translate', 'copy_only', 'ignore']), default='all', help='Filter by file type')
@click.help_option('--help', '-h')
def main(upstream_ref: str, meta_branch: str, output: str, output_format: str, filter_type: str):
    """Discover changes between upstream and current repository.
    
    This tool analyzes differences between the upstream repository and the current
    state to determine what files need translation, copying, or other processing.
    
    Examples:
        python discover_changes.py
        python discover_changes.py --upstream-ref upstream/develop
        python discover_changes.py --format summary --filter-type translate
        python discover_changes.py -o my_changes.json
    """
    
    try:
        # Initialize discoverer
        discoverer = ChangeDiscoverer()
        
        # Ensure upstream is configured
        click.echo("Setting up upstream remote...")
        if not discoverer.git_utils.add_upstream_remote():
            click.echo("Warning: Could not add upstream remote", err=True)
        
        if not discoverer.git_utils.fetch_upstream():
            click.echo("Warning: Could not fetch from upstream", err=True)
        
        # Discover changes
        click.echo(f"Discovering changes from {upstream_ref}...")
        changes = discoverer.discover_changes(upstream_ref, meta_branch)
        
        # Set output file
        if not output:
            output = str(config.output_dir / "changes.json")
        
        # Output results
        if output_format == 'json':
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(changes, f, indent=2, ensure_ascii=False)
            click.echo(f"Changes written to: {output}")
        
        elif output_format == 'summary':
            _print_summary(changes, filter_type)
        
        return 0
        
    except Exception as e:
        click.echo(f"Error discovering changes: {e}", err=True)
        return 1


def _print_summary(changes: Dict[str, Any], filter_type: str):
    """Print summary of changes."""
    click.echo(f"\n=== Change Discovery Summary ===")
    click.echo(f"Upstream ref: {changes['upstream_ref']}")
    click.echo(f"Meta branch: {changes['meta_branch']}")
    
    for category, files in changes["files"].items():
        if filter_type != 'all' and category != filter_type:
            continue
        
        click.echo(f"\n{category.upper()} FILES ({len(files)}):")
        
        for file_info in files:
            path = file_info["path"]
            status = file_info["status"]
            summary = file_info.get("summary", {})
            
            click.echo(f"  {path} ({status})")
            
            if summary.get("total_operations", 0) > 0:
                click.echo(f"    - Added: {summary.get('added_lines', 0)} lines")
                click.echo(f"    - Removed: {summary.get('removed_lines', 0)} lines")
                click.echo(f"    - Modified: {summary.get('modified_lines', 0)} lines")
                click.echo(f"    - Minor edits: {summary.get('minor_edits', 0)}")
                click.echo(f"    - Major changes: {summary.get('major_changes', 0)}")


if __name__ == '__main__':
    exit(main())