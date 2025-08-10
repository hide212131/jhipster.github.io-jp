"""File filtering utilities for translation system."""

import re
from pathlib import Path
from typing import List, Set

from config import config


class FileFilters:
    """Utilities for filtering files for translation."""

    def __init__(self):
        self.target_extensions = set(config.target_extensions)
        self.exclude_patterns = self._compile_exclude_patterns()

    def _compile_exclude_patterns(self) -> List[re.Pattern]:
        """Compile exclude path patterns."""
        patterns = []
        for pattern in config.exclude_paths:
            # Convert glob-like patterns to regex
            regex_pattern = pattern.replace("*", ".*").replace("?", ".")
            if not regex_pattern.endswith("/"):
                regex_pattern += "$"
            patterns.append(re.compile(regex_pattern))
        return patterns

    def is_translatable_file(self, file_path: str) -> bool:
        """Check if file should be translated."""
        path = Path(file_path)

        # Check extension
        if path.suffix not in self.target_extensions:
            return False

        # Check exclude patterns
        path_str = str(path)
        for pattern in self.exclude_patterns:
            if pattern.search(path_str):
                return False

        return True

    def is_documentation_file(self, file_path: str) -> bool:
        """Check if file is a documentation file."""
        return self.is_translatable_file(file_path)

    def filter_changed_files(self, files: List[str]) -> dict:
        """Categorize changed files into translatable and non-translatable."""
        result = {"translatable": [], "copy_only": []}

        for file_path in files:
            if self.is_translatable_file(file_path):
                result["translatable"].append(file_path)
            else:
                result["copy_only"].append(file_path)

        return result

    def get_docs_files(self, directory: str = "docs") -> List[str]:
        """Get all documentation files in directory."""
        docs_path = Path(directory)
        if not docs_path.exists():
            return []

        files = []
        for path in docs_path.rglob("*"):
            if path.is_file() and self.is_translatable_file(str(path)):
                files.append(str(path))

        return sorted(files)
