#!/usr/bin/env python3
"""
Sync tool for jp repository with development mode support.

Provides sync functionality with flexible filtering options for development:
- Development mode with commit, file, and count filtering
- Production mode for full sync operations
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

# Add tools directory to path for importing dev_filter
sys.path.insert(0, str(Path(__file__).parent))

from dev_filter import DevFilter


class SyncRunner:
    """Main sync runner with development mode support."""
    
    def __init__(self, mode: str = 'prod', verbose: bool = False):
        """
        Initialize sync runner.
        
        Args:
            mode: Run mode ('dev' or 'prod')
            verbose: Enable verbose output
        """
        self.mode = mode
        self.verbose = verbose
        
    def log(self, message: str, force: bool = False):
        """Log message if verbose mode is enabled."""
        if self.verbose or force:
            print(f"[{self.mode.upper()}] {message}")
    
    def run_dev_mode(self, dev_filter: DevFilter):
        """
        Run sync in development mode with filtering.
        
        Args:
            dev_filter: Configured development filter
        """
        self.log("Starting development mode sync with filters")
        
        # Get sample data for demonstration
        all_commits = self._get_recent_commits()
        all_files = dev_filter.get_untranslated_files()
        
        self.log(f"Found {len(all_commits)} recent commits")
        self.log(f"Found {len(all_files)} files to process")
        
        # Apply filters
        filtered_data = dev_filter.apply_all_filters(
            commits=all_commits,
            files=all_files
        )
        
        filtered_commits = filtered_data.get('commits', [])
        filtered_files = filtered_data.get('files', [])
        
        self.log(f"After filtering: {len(filtered_commits)} commits, {len(filtered_files)} files")
        
        # Process filtered items
        self._process_commits(filtered_commits)
        self._process_files(filtered_files)
        
        self.log("Development mode sync completed", force=True)
    
    def run_prod_mode(self):
        """Run sync in production mode (full sync)."""
        self.log("Starting production mode sync")
        
        # Get all data for full sync
        all_commits = self._get_recent_commits()
        all_files = DevFilter().get_untranslated_files()
        
        self.log(f"Processing {len(all_commits)} commits and {len(all_files)} files")
        
        # Process all items without filtering
        self._process_commits(all_commits)
        self._process_files(all_files)
        
        self.log("Production mode sync completed", force=True)
    
    def _get_recent_commits(self, count: int = 20) -> List[str]:
        """
        Get recent commits (placeholder implementation).
        
        Args:
            count: Number of recent commits to get
            
        Returns:
            List of commit hashes
        """
        import subprocess
        
        try:
            cmd = ['git', 'rev-list', '--max-count', str(count), 'HEAD']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            commits = result.stdout.strip().split('\n') if result.stdout.strip() else []
            return [c for c in commits if c]  # Filter out empty strings
        except subprocess.CalledProcessError:
            self.log("Warning: Could not get git commits (not in git repository?)")
            # Return sample commits for demonstration
            return [f"commit_{i:03d}" for i in range(1, count + 1)]
    
    def _process_commits(self, commits: List[str]):
        """
        Process filtered commits.
        
        Args:
            commits: List of commit hashes to process
        """
        self.log(f"Processing {len(commits)} commits:")
        for i, commit in enumerate(commits):
            self.log(f"  {i+1:2d}. {commit[:12]}...")
            # Here would be the actual sync logic for commits
    
    def _process_files(self, files: List[str]):
        """
        Process filtered files.
        
        Args:
            files: List of file paths to process
        """
        self.log(f"Processing {len(files)} files:")
        for i, file_path in enumerate(files):
            self.log(f"  {i+1:2d}. {file_path}")
            # Here would be the actual sync logic for files


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Sync tool for jp repository with development mode support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Production mode (full sync)
  python run_sync.py --mode prod
  
  # Development mode with filters
  python run_sync.py --mode dev --limit 5
  python run_sync.py --mode dev --before abc123 --limit 10
  python run_sync.py --mode dev --paths "*.md" "pages/*"
  python run_sync.py --mode dev --before HEAD~10 --limit 5 --paths "*.md"
        '''
    )
    
    parser.add_argument(
        '--mode',
        choices=['dev', 'prod'],
        default='prod',
        help='Run mode: dev (development with filters) or prod (production, full sync)'
    )
    
    parser.add_argument(
        '--before',
        type=str,
        help='Filter commits before specified commit (dev mode only)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of items to process (dev mode only)'
    )
    
    parser.add_argument(
        '--paths',
        nargs='*',
        help='Filter by file paths/patterns (dev mode only)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser.parse_args()


def validate_dev_args(args: argparse.Namespace) -> bool:
    """
    Validate development mode arguments.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        True if arguments are valid
    """
    if args.mode != 'dev':
        return True
    
    # Check if at least one dev filter is specified
    dev_filters = [args.before, args.limit, args.paths]
    if not any(dev_filters):
        print("Error: Development mode requires at least one filter option (--before, --limit, or --paths)")
        return False
    
    # Validate limit is positive
    if args.limit is not None and args.limit <= 0:
        print("Error: --limit must be a positive integer")
        return False
    
    return True


def main():
    """Main entry point."""
    args = parse_args()
    
    # Validate arguments
    if not validate_dev_args(args):
        sys.exit(1)
    
    # Create sync runner
    runner = SyncRunner(mode=args.mode, verbose=args.verbose)
    
    try:
        if args.mode == 'dev':
            # Create development filter with specified options
            dev_filter = DevFilter(
                before=args.before,
                limit=args.limit,
                paths=args.paths
            )
            runner.run_dev_mode(dev_filter)
        else:
            runner.run_prod_mode()
            
    except KeyboardInterrupt:
        print("\nSync interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during sync: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()