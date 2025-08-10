#!/usr/bin/env python3
"""
Change application utilities for JHipster translation tools.
Applies translated changes back to files.
"""

from typing import List, Dict, Optional
from pathlib import Path
from tools.discover_changes import FileChange


class ChangeApplicator:
    """Applies translated changes to files."""
    
    def __init__(self, repo_path: str = "."):
        """Initialize change applicator."""
        self.repo_path = Path(repo_path)
    
    def apply_file_change(self, file_change: FileChange, translated_content: str) -> bool:
        """Apply a translated file change."""
        file_path = self.repo_path / file_change.file_path
        
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write translated content
            file_path.write_text(translated_content, encoding='utf-8')
            
            return True
        except Exception as e:
            print(f"Error applying change to {file_change.file_path}: {e}")
            return False
    
    def apply_multiple_changes(self, changes_and_translations: List[tuple]) -> Dict[str, bool]:
        """Apply multiple file changes with their translations."""
        results = {}
        
        for file_change, translated_content in changes_and_translations:
            success = self.apply_file_change(file_change, translated_content)
            results[file_change.file_path] = success
        
        return results
    
    def create_backup(self, file_path: str) -> Optional[str]:
        """Create backup of existing file before applying changes."""
        source_path = self.repo_path / file_path
        
        if not source_path.exists():
            return None
        
        backup_path = source_path.with_suffix(source_path.suffix + '.backup')
        
        try:
            backup_path.write_text(source_path.read_text(encoding='utf-8'), encoding='utf-8')
            return str(backup_path)
        except Exception as e:
            print(f"Warning: Could not create backup for {file_path}: {e}")
            return None
    
    def restore_backup(self, backup_path: str) -> bool:
        """Restore file from backup."""
        backup_file = Path(backup_path)
        original_file = backup_file.with_suffix('')
        
        try:
            original_file.write_text(backup_file.read_text(encoding='utf-8'), encoding='utf-8')
            backup_file.unlink()  # Remove backup after restoration
            return True
        except Exception as e:
            print(f"Error restoring backup {backup_path}: {e}")
            return False
    
    def dry_run_changes(self, changes_and_translations: List[tuple]) -> Dict[str, str]:
        """Simulate applying changes without actually writing files."""
        results = {}
        
        for file_change, translated_content in changes_and_translations:
            # Just record what would be written
            results[file_change.file_path] = {
                'change_type': file_change.change_type,
                'would_write': len(translated_content) if translated_content else 0,
                'preview': translated_content[:200] + "..." if translated_content and len(translated_content) > 200 else translated_content
            }
        
        return results
    
    def validate_changes(self, changes_and_translations: List[tuple]) -> List[str]:
        """Validate changes before applying them."""
        errors = []
        
        for file_change, translated_content in changes_and_translations:
            # Check if translated content is valid
            if not translated_content and file_change.change_type != "deleted":
                errors.append(f"Empty translated content for {file_change.file_path}")
            
            # Check if file path is safe
            file_path = Path(file_change.file_path)
            if file_path.is_absolute() or '..' in file_path.parts:
                errors.append(f"Unsafe file path: {file_change.file_path}")
            
            # Check if target directory would be valid
            target_path = self.repo_path / file_change.file_path
            try:
                target_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create directory for {file_change.file_path}: {e}")
        
        return errors