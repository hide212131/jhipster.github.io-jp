"""File filtering utilities for translation pipeline."""

from typing import List, Set
from pathlib import Path
from config import config


class FileFilter:
    """Filter files for translation processing."""
    
    def __init__(self):
        """Initialize file filter with configuration."""
        self.target_extensions = config.target_extensions
        self.excluded_paths = config.excluded_paths
        self.excluded_extensions = config.excluded_extensions
    
    def is_translation_target(self, file_path: str) -> bool:
        """Check if file should be translated."""
        path = Path(file_path)
        
        # Check if path is excluded
        for excluded_path in self.excluded_paths:
            if excluded_path in str(path):
                return False
        
        # Check extension
        if path.suffix.lower() in self.target_extensions:
            return True
        
        return False
    
    def is_copy_only(self, file_path: str) -> bool:
        """Check if file should be copied without translation."""
        path = Path(file_path)
        
        # Check if path is excluded (should be ignored completely)
        for excluded_path in self.excluded_paths:
            if excluded_path in str(path):
                return False
        
        # Check if it's a translation target
        if self.is_translation_target(file_path):
            return False
        
        # Check if it's an excluded extension (should be ignored, not copied)
        if path.suffix.lower() in self.excluded_extensions:
            return False
        
        # Other files should be copied
        return True
    
    def should_ignore(self, file_path: str) -> bool:
        """Check if file should be completely ignored."""
        path = Path(file_path)
        
        # Check excluded paths
        for excluded_path in self.excluded_paths:
            if excluded_path in str(path):
                return True
        
        # Check excluded extensions
        if path.suffix.lower() in self.excluded_extensions:
            return True
        
        return False
    
    def filter_files(self, file_paths: List[str]) -> dict:
        """Filter files into categories."""
        result = {
            "translate": [],
            "copy_only": [],
            "ignore": []
        }
        
        for file_path in file_paths:
            if self.should_ignore(file_path):
                result["ignore"].append(file_path)
            elif self.is_translation_target(file_path):
                result["translate"].append(file_path)
            elif self.is_copy_only(file_path):
                result["copy_only"].append(file_path)
            else:
                result["ignore"].append(file_path)
        
        return result
    
    def get_document_files(self, directory: str) -> List[str]:
        """Get all document files in directory recursively."""
        doc_files = []
        path = Path(directory)
        
        if not path.exists():
            return doc_files
        
        for file_path in path.rglob("*"):
            if file_path.is_file() and self.is_translation_target(str(file_path)):
                doc_files.append(str(file_path.relative_to(path)))
        
        return doc_files