"""Apply changes based on discovery results."""

import click
import json
from typing import Dict, List, Any, Optional
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
        self.similarity_threshold = 0.98  # Threshold for minor changes (軽微変更)
    
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
                if result["action"] in ["translated"]:
                    results["statistics"]["translated"] += 1
                elif result["action"] in ["kept_existing", "kept_existing_llm"]:
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
        """Apply changes for a specific file with operation-level handling."""
        file_path = file_info["path"]
        operations = file_info.get("operations", [])
        
        if not operations:
            return {"action": "no_changes", "details": "No operations to apply"}
        
        # Get existing Japanese translation to preserve when appropriate
        existing_translation = self._get_existing_translation(file_path)
        
        # Analyze operations to determine strategy
        strategies = [op.get("strategy", "retranslate") for op in operations]
        
        # Handle based on operation strategies
        if all(strategy == "keep_existing" for strategy in strategies):
            # All operations are keep_existing - preserve existing translation
            if existing_translation:
                self._write_file_content(file_path, existing_translation)
                return {
                    "action": "kept_existing",
                    "details": f"Preserved existing translation for {len(operations)} operations",
                    "operations_count": len(operations),
                    "strategies": strategies
                }
            else:
                # No existing translation, need to translate
                return self._translate_file_content(file_path, operations)
        
        elif any(strategy in ["translate_new", "retranslate"] for strategy in strategies):
            # Contains operations requiring translation
            return self._handle_translation_operations(file_path, operations, existing_translation)
        
        elif all(strategy == "delete_existing" for strategy in strategies):
            # All operations are deletions
            return {
                "action": "kept_existing", 
                "details": f"File content removed by {len(operations)} delete operations",
                "operations_count": len(operations),
                "strategies": strategies
            }
        
        else:
            # Mixed strategies - handle with smart operation-level processing
            return self._handle_mixed_operations(file_path, operations, existing_translation)
    
    def _get_existing_translation(self, file_path: str) -> Optional[str]:
        """Get existing Japanese translation content."""
        try:
            # Try to get current file content (existing translation)
            current_content = self.git_utils.get_file_content(file_path, "HEAD")
            return current_content
        except Exception:
            # No existing translation
            return None
    
    def _write_file_content(self, file_path: str, content: str) -> None:
        """Write content to file."""
        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _translate_file_content(self, file_path: str, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Translate entire file content."""
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
        self._write_file_content(file_path, translated_content)
        
        return {
            "action": "translated",
            "details": f"Translated entire file with {len(operations)} operations",
            "operations_count": len(operations)
        }
    
    def _handle_translation_operations(self, file_path: str, operations: List[Dict[str, Any]], 
                                     existing_translation: Optional[str]) -> Dict[str, Any]:
        """Handle operations that require translation with smart strategy selection."""
        # Check for replace operations that might need LLM semantic analysis
        replace_ops = [op for op in operations if op.get("operation") == "replace"]
        
        needs_llm_check = False
        for op in replace_ops:
            strategy = op.get("strategy", "retranslate")
            similarity = op.get("similarity_ratio", 0.0)
            
            # If similarity is borderline or strategy is retranslate, consider LLM check
            if strategy == "retranslate" and 0.8 <= similarity < self.similarity_threshold:
                needs_llm_check = True
                break
        
        # For replace operations near threshold, use LLM to check semantic change
        if needs_llm_check and existing_translation:
            old_content = "\n".join(replace_ops[0].get("old_lines", []))
            new_content = "\n".join(replace_ops[0].get("new_lines", []))
            
            # LLM semantic change check (意味変化疑い時はLLMでYES/NO判定)
            if self.translator.check_semantic_change(old_content, new_content):
                # Semantic change detected - retranslate
                return self._translate_file_content(file_path, operations)
            else:
                # No semantic change - preserve existing translation
                self._write_file_content(file_path, existing_translation)
                return {
                    "action": "kept_existing_llm",
                    "details": f"LLM determined no semantic change, preserved existing translation",
                    "operations_count": len(operations),
                    "llm_checked": True
                }
        
        # Regular translation handling
        return self._translate_file_content(file_path, operations)
    
    def _handle_mixed_operations(self, file_path: str, operations: List[Dict[str, Any]], 
                                existing_translation: Optional[str]) -> Dict[str, Any]:
        """Handle files with mixed operation types (equal/insert/delete/replace)."""
        # Categorize operations by strategy
        keep_ops = [op for op in operations if op.get("strategy") == "keep_existing"]
        translate_ops = [op for op in operations if op.get("strategy") in ["translate_new", "retranslate"]]
        delete_ops = [op for op in operations if op.get("strategy") == "delete_existing"]
        
        # If there are any operations requiring translation, translate the whole file
        if translate_ops:
            return self._translate_file_content(file_path, operations)
        
        # If only keep and delete operations, preserve existing where possible
        if existing_translation and (keep_ops or delete_ops):
            self._write_file_content(file_path, existing_translation)
            return {
                "action": "kept_existing",
                "details": f"Mixed operations: kept existing for {len(keep_ops)} ops, deleted {len(delete_ops)} ops",
                "operations_count": len(operations),
                "mixed_strategies": True
            }
        
        # Fallback to translation
        return self._translate_file_content(file_path, operations)
    
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