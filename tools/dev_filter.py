#!/usr/bin/env python3
"""
Development filter utilities for JHipster translation tools.
Provides filtering and debugging utilities for development.
"""

from typing import List, Dict, Any, Optional
import json
from pathlib import Path


class DevFilter:
    """Development utilities for filtering and debugging."""
    
    def __init__(self, debug_mode: bool = False):
        """Initialize development filter."""
        self.debug_mode = debug_mode
        self.filter_cache = {}
    
    def filter_files_for_dev(self, file_paths: List[str], limit: Optional[int] = None) -> List[str]:
        """Filter files for development (e.g., limit to first N files)."""
        if limit is not None:
            return file_paths[:limit]
        return file_paths
    
    def create_test_subset(self, data: List[Any], subset_size: int = 5) -> List[Any]:
        """Create a small subset of data for testing."""
        return data[:subset_size]
    
    def log_debug_info(self, message: str, data: Any = None):
        """Log debug information if debug mode is enabled."""
        if self.debug_mode:
            print(f"[DEBUG] {message}")
            if data is not None:
                if isinstance(data, (dict, list)):
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                else:
                    print(data)
    
    def create_dry_run_summary(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create summary of operations that would be performed."""
        summary = {
            'total_operations': len(operations),
            'operations_by_type': {},
            'affected_files': set(),
            'estimated_time': 0
        }
        
        for op in operations:
            op_type = op.get('type', 'unknown')
            summary['operations_by_type'][op_type] = summary['operations_by_type'].get(op_type, 0) + 1
            
            if 'file_path' in op:
                summary['affected_files'].add(op['file_path'])
            
            # Rough time estimation
            if op_type == 'translate':
                summary['estimated_time'] += 5  # 5 seconds per translation
            else:
                summary['estimated_time'] += 1  # 1 second for other operations
        
        summary['affected_files'] = list(summary['affected_files'])
        return summary
    
    def save_debug_data(self, data: Any, filename: str):
        """Save debug data to file."""
        if not self.debug_mode:
            return
        
        debug_dir = Path('.') / 'debug_output'
        debug_dir.mkdir(exist_ok=True)
        
        debug_file = debug_dir / filename
        
        try:
            if isinstance(data, (dict, list)):
                with open(debug_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(str(data))
            
            self.log_debug_info(f"Debug data saved to {debug_file}")
        except Exception as e:
            self.log_debug_info(f"Failed to save debug data: {e}")
    
    def validate_environment(self) -> Dict[str, bool]:
        """Validate development environment setup."""
        checks = {
            'git_repo': self._check_git_repo(),
            'python_version': self._check_python_version(),
            'required_packages': self._check_required_packages(),
            'write_permissions': self._check_write_permissions(),
        }
        
        self.log_debug_info("Environment validation", checks)
        return checks
    
    def _check_git_repo(self) -> bool:
        """Check if we're in a git repository."""
        return (Path('.') / '.git').exists()
    
    def _check_python_version(self) -> bool:
        """Check if Python version is adequate."""
        import sys
        return sys.version_info >= (3, 8)
    
    def _check_required_packages(self) -> bool:
        """Check if required packages are available."""
        required_packages = ['google.generativeai']
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                return False
        return True
    
    def _check_write_permissions(self) -> bool:
        """Check if we have write permissions in current directory."""
        try:
            test_file = Path('.') / '.write_test'
            test_file.write_text('test')
            test_file.unlink()
            return True
        except Exception:
            return False
    
    def create_sample_data(self) -> Dict[str, Any]:
        """Create sample data for testing."""
        return {
            'sample_files': [
                'docs/sample.md',
                'pages/test.md'
            ],
            'sample_changes': [
                {
                    'file_path': 'docs/sample.md',
                    'change_type': 'modified',
                    'old_content': '# Hello World\nThis is a test.',
                    'new_content': '# Hello World\nThis is an updated test.'
                }
            ],
            'sample_translation': {
                'original': 'Hello World',
                'translated': 'こんにちは世界'
            }
        }