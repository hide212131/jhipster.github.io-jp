"""Apply changes based on discovery results."""

import click
import json
from typing import Dict, List, Any
from pathlib import Path
from git_utils import GitUtils
from translate_blockwise import BlockwiseTranslator
from config import config


class ChangeApplicator:
    """Apply changes based on discovery results."""
    
    def __init__(self):
        """Initialize change applicator."""
        self.git_utils = GitUtils()
        self.translator = BlockwiseTranslator()
    
    def apply_changes(self, changes_file: str, target_files: List[str] = None) -> Dict[str, Any]:
        """Apply changes from discovery results."""
        # Load changes
        with open(changes_file, 'r', encoding='utf-8') as f:
            changes = json.load(f)
        
        results = {
            "processed_files": [],
            "skipped_files": [],
            "errors": [],
            "statistics": {
                "translated": 0,
                "copied": 0,
                "kept_existing": 0,
                "deleted": 0
            }
        }
        
        # Process translation targets
        translate_files = changes["files"].get("translate", [])
        for file_info in translate_files:
            file_path = file_info["path"]
            
            # Skip if not in target files list
            if target_files and file_path not in target_files:
                results["skipped_files"].append(file_path)
                continue
            
            try:
                result = self._apply_file_changes(file_info)
                results["processed_files"].append({
                    "file": file_path,
                    "result": result
                })
                
                # Update statistics
                if result["action"] == "translated":
                    results["statistics"]["translated"] += 1
                elif result["action"] == "kept_existing":
                    results["statistics"]["kept_existing"] += 1
                    
            except Exception as e:
                error_info = {
                    "file": file_path,
                    "error": str(e)
                }
                results["errors"].append(error_info)
        
        # Process copy-only files
        copy_files = changes["files"].get("copy_only", [])
        for file_info in copy_files:
            file_path = file_info["path"]
            
            if target_files and file_path not in target_files:
                results["skipped_files"].append(file_path)
                continue
            
            try:
                self._copy_file(file_info)
                results["processed_files"].append({
                    "file": file_path,
                    "result": {"action": "copied"}
                })
                results["statistics"]["copied"] += 1
                
            except Exception as e:
                results["errors"].append({
                    "file": file_path,
                    "error": str(e)
                })
        
        return results
    
    def _apply_file_changes(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Apply changes for a specific file."""
        file_path = file_info["path"]
        operations = file_info.get("operations", [])
        
        if not operations:
            return {"action": "no_changes", "details": "No operations to apply"}
        
        # Analyze operations to determine strategy
        needs_translation = any(
            op["strategy"] in ["translate_new", "retranslate"] 
            for op in operations
        )
        
        if needs_translation:
            # Get upstream content
            upstream_content = self.git_utils.get_file_content(file_path, "upstream/main")
            if upstream_content is None:
                raise Exception(f"Could not get upstream content for {file_path}")
            
            # Translate content
            translated_content = self.translator.translate_file_content(
                upstream_content, 
                context=f"File: {file_path}"
            )
            
            # Write translated content
            output_path = Path(file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(translated_content)
            
            return {
                "action": "translated",
                "details": f"Translated {len(operations)} operations",
                "operations_count": len(operations)
            }
        else:
            # Keep existing content (all operations are keep_existing or delete_existing)
            return {
                "action": "kept_existing",
                "details": "No translation needed",
                "operations_count": len(operations)
            }
    
    def _copy_file(self, file_info: Dict[str, Any]) -> None:
        """Copy file without translation."""
        file_path = file_info["path"]
        
        # Get upstream content
        upstream_content = self.git_utils.get_file_content(file_path, "upstream/main")
        if upstream_content is None:
            raise Exception(f"Could not get upstream content for {file_path}")
        
        # Write content as-is
        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Handle binary files
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(upstream_content)
        except UnicodeDecodeError:
            # Handle as binary
            with open(output_path, 'wb') as f:
                f.write(upstream_content.encode('utf-8'))


@click.command()
@click.option('--changes-file', '-c', required=True, help='Changes file from discover_changes')
@click.option('--target-files', '-f', multiple=True, help='Specific files to process (default: all)')
@click.option('--output', '-o', help='Output file for results (default: .out/apply_results.json)')
@click.option('--dry-run', is_flag=True, help='Show what would be applied without doing it')
@click.option('--commit', is_flag=True, help='Commit changes after applying')
@click.option('--commit-message', default='Apply translation changes', help='Commit message')
@click.help_option('--help', '-h')
def main(changes_file: str, target_files: tuple, output: str, dry_run: bool, commit: bool, commit_message: str):
    """Apply changes based on discovery results.
    
    This tool takes the output from discover_changes and applies the necessary
    translations, copies, and other changes to the repository.
    
    Examples:
        python apply_changes.py -c .out/changes.json
        python apply_changes.py -c changes.json -f docs/readme.md -f docs/guide.md
        python apply_changes.py -c changes.json --dry-run
        python apply_changes.py -c changes.json --commit
    """
    
    try:
        # Validate inputs
        changes_path = Path(changes_file)
        if not changes_path.exists():
            click.echo(f"Error: Changes file '{changes_file}' not found", err=True)
            return 1
        
        target_files_list = list(target_files) if target_files else None
        
        if not output:
            output = str(config.output_dir / "apply_results.json")
        
        click.echo(f"Loading changes from: {changes_file}")
        if target_files_list:
            click.echo(f"Processing {len(target_files_list)} specific files")
        else:
            click.echo("Processing all files from changes")
        
        if dry_run:
            click.echo("DRY RUN - No files will be modified")
            # TODO: Implement dry run preview
            return 0
        
        # Apply changes
        applicator = ChangeApplicator()
        results = applicator.apply_changes(changes_file, target_files_list)
        
        # Save results
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Print summary
        stats = results["statistics"]
        click.echo(f"\n=== Application Results ===")
        click.echo(f"Processed files: {len(results['processed_files'])}")
        click.echo(f"Skipped files: {len(results['skipped_files'])}")
        click.echo(f"Errors: {len(results['errors'])}")
        click.echo(f"\nStatistics:")
        click.echo(f"  - Translated: {stats['translated']}")
        click.echo(f"  - Copied: {stats['copied']}")
        click.echo(f"  - Kept existing: {stats['kept_existing']}")
        click.echo(f"  - Deleted: {stats['deleted']}")
        
        if results["errors"]:
            click.echo(f"\nErrors:")
            for error in results["errors"]:
                click.echo(f"  - {error['file']}: {error['error']}")
        
        click.echo(f"\nResults saved to: {output}")
        
        # Commit if requested
        if commit and not dry_run:
            click.echo(f"\nCommitting changes...")
            if applicator.git_utils.commit_changes(commit_message):
                click.echo("Changes committed successfully")
            else:
                click.echo("No changes to commit")
        
        return 0
        
    except Exception as e:
        click.echo(f"Error applying changes: {e}", err=True)
        return 1


if __name__ == '__main__':
    exit(main())