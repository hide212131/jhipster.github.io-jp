#!/usr/bin/env python3
"""
Main synchronization script for JHipster translation tools.
Orchestrates the translation workflow from change discovery to PR creation.
"""

import argparse
import sys
from typing import List, Optional
from pathlib import Path

# Add the project root to the path for imports
if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

# Import all the tools
from tools.config import config
from tools.git_utils import GitUtils
from tools.file_filters import FileFilters  
from tools.discover_changes import ChangeDiscoverer, FileChange
from tools.translate_linewise import LinewiseTranslator
from tools.apply_changes import ChangeApplicator
from tools.pr_body import PRBodyGenerator
from tools.verify_alignment import TranslationVerifier
from tools.dev_filter import DevFilter


class SyncRunner:
    """Main synchronization workflow runner."""
    
    def __init__(self, dry_run: bool = False, debug: bool = False, limit: Optional[int] = None):
        """Initialize sync runner with options."""
        self.dry_run = dry_run
        self.debug = debug
        self.limit = limit
        
        # Initialize components
        self.git_utils = GitUtils()
        self.file_filters = FileFilters()
        self.change_discoverer = ChangeDiscoverer()
        self.translator = LinewiseTranslator(use_mock_llm=dry_run or not config.gemini_api_key)
        self.change_applicator = ChangeApplicator()
        self.pr_generator = PRBodyGenerator()
        self.verifier = TranslationVerifier()
        self.dev_filter = DevFilter(debug_mode=debug)
    
    def run_sync(self, base_ref: str = "main", target_ref: str = "HEAD") -> bool:
        """Run the complete synchronization workflow."""
        try:
            self.dev_filter.log_debug_info("Starting synchronization workflow")
            
            # Step 1: Validate environment
            if not self._validate_environment():
                return False
            
            # Step 2: Discover changes
            changes = self._discover_changes(base_ref, target_ref)
            if not changes:
                print("No translatable changes found.")
                return True
            
            # Step 3: Process translations
            translations = self._process_translations(changes)
            
            # Step 4: Verify translations
            verification_results = self._verify_translations(changes, translations)
            
            # Step 5: Apply changes (or dry run)
            if self.dry_run:
                self._perform_dry_run(changes, translations)
            else:
                success = self._apply_changes(changes, translations)
                if not success:
                    return False
            
            # Step 6: Generate PR information
            self._generate_pr_info(changes)
            
            print("✅ Synchronization completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Synchronization failed: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return False
    
    def _validate_environment(self) -> bool:
        """Validate environment setup."""
        self.dev_filter.log_debug_info("Validating environment")
        
        if not self.git_utils.is_git_repo():
            print("❌ Not in a git repository")
            return False
        
        env_checks = self.dev_filter.validate_environment()
        if not all(env_checks.values()):
            print("❌ Environment validation failed")
            for check, passed in env_checks.items():
                status = "✅" if passed else "❌"
                print(f"  {status} {check}")
            return False
        
        print("✅ Environment validation passed")
        return True
    
    def _discover_changes(self, base_ref: str, target_ref: str) -> List[FileChange]:
        """Discover translatable changes."""
        self.dev_filter.log_debug_info(f"Discovering changes between {base_ref} and {target_ref}")
        
        all_changes = self.change_discoverer.discover_changes(base_ref, target_ref)
        translatable_changes = [c for c in all_changes if self.file_filters.is_translatable(c.file_path)]
        
        # Apply development limits if specified
        if self.limit:
            translatable_changes = self.dev_filter.filter_files_for_dev(translatable_changes, self.limit)
        
        change_summary = self.change_discoverer.get_change_summary(translatable_changes)
        print(f"📋 Found {len(translatable_changes)} translatable changes:")
        for change_type, count in change_summary.items():
            if count > 0:
                print(f"  - {change_type}: {count} files")
        
        self.dev_filter.save_debug_data(
            [c._asdict() for c in translatable_changes], 
            "discovered_changes.json"
        )
        
        return translatable_changes
    
    def _process_translations(self, changes: List[FileChange]) -> List[str]:
        """Process translations for all changes."""
        self.dev_filter.log_debug_info(f"Processing translations for {len(changes)} files")
        
        translations = []
        for i, change in enumerate(changes):
            print(f"🌐 Translating {i+1}/{len(changes)}: {change.file_path}")
            
            if change.change_type == "deleted":
                translations.append("")  # Empty content for deleted files
            elif change.new_content:
                try:
                    translated = self.translator.translate_file_content(change.new_content)
                    translations.append(translated)
                except Exception as e:
                    print(f"⚠️ Translation failed for {change.file_path}: {e}")
                    translations.append(change.new_content)  # Use original on failure
            else:
                translations.append("")
        
        return translations
    
    def _verify_translations(self, changes: List[FileChange], translations: List[str]) -> dict:
        """Verify translation quality."""
        self.dev_filter.log_debug_info("Verifying translation quality")
        
        verification_pairs = []
        for change, translation in zip(changes, translations):
            if change.new_content and translation:
                verification_pairs.append((change.new_content, translation))
        
        results = self.verifier.verify_batch_translations(verification_pairs)
        
        # Print verification summary
        valid_count = sum(1 for r in results.values() if r.is_valid)
        total_count = len(results)
        
        print(f"🔍 Translation verification: {valid_count}/{total_count} passed")
        
        if self.debug:
            report = self.verifier.generate_verification_report(results)
            print(report)
            self.dev_filter.save_debug_data(
                {k: v._asdict() for k, v in results.items()}, 
                "verification_results.json"
            )
        
        return results
    
    def _perform_dry_run(self, changes: List[FileChange], translations: List[str]):
        """Perform dry run without actually applying changes."""
        print("🧪 Performing dry run (no files will be modified)")
        
        changes_and_translations = list(zip(changes, translations))
        dry_run_results = self.change_applicator.dry_run_changes(changes_and_translations)
        
        print("📊 Dry run summary:")
        for file_path, result in dry_run_results.items():
            print(f"  📄 {file_path}: {result['change_type']} ({result['would_write']} chars)")
        
        self.dev_filter.save_debug_data(dry_run_results, "dry_run_results.json")
    
    def _apply_changes(self, changes: List[FileChange], translations: List[str]) -> bool:
        """Apply translated changes to files."""
        self.dev_filter.log_debug_info("Applying changes to files")
        
        changes_and_translations = list(zip(changes, translations))
        
        # Validate changes first
        validation_errors = self.change_applicator.validate_changes(changes_and_translations)
        if validation_errors:
            print("❌ Validation errors found:")
            for error in validation_errors:
                print(f"  - {error}")
            return False
        
        # Apply changes
        results = self.change_applicator.apply_multiple_changes(changes_and_translations)
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        print(f"📝 Applied changes: {success_count}/{total_count} successful")
        
        if success_count < total_count:
            print("⚠️ Some changes failed to apply:")
            for file_path, success in results.items():
                if not success:
                    print(f"  - {file_path}")
        
        return success_count == total_count
    
    def _generate_pr_info(self, changes: List[FileChange]):
        """Generate PR title and body."""
        change_summary = self.change_discoverer.get_change_summary(changes)
        
        title = self.pr_generator.generate_pr_title(changes, change_summary)
        body = self.pr_generator.generate_pr_body(changes, change_summary)
        commit_message = self.pr_generator.generate_commit_message(changes)
        branch_name = self.pr_generator.generate_branch_name(changes)
        
        print("\n📋 Generated PR Information:")
        print(f"Branch: {branch_name}")
        print(f"Title: {title}")
        print(f"Commit: {commit_message}")
        
        if self.debug:
            print("\nPR Body:")
            print(body)
            
            self.dev_filter.save_debug_data({
                'title': title,
                'body': body,
                'commit_message': commit_message,
                'branch_name': branch_name
            }, "pr_info.json")


def main():
    """Main entry point for the sync script."""
    parser = argparse.ArgumentParser(
        description="JHipster translation synchronization tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/run_sync.py --help
  python tools/run_sync.py --dry-run
  python tools/run_sync.py --debug --limit 5
  python tools/run_sync.py --base-ref origin/main
        """
    )
    
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Perform dry run without applying changes'
    )
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Enable debug mode with verbose output'
    )
    parser.add_argument(
        '--limit', 
        type=int,
        help='Limit number of files to process (for development)'
    )
    parser.add_argument(
        '--base-ref',
        default='main',
        help='Base git reference for comparison (default: main)'
    )
    parser.add_argument(
        '--target-ref',
        default='HEAD',
        help='Target git reference for comparison (default: HEAD)'
    )
    
    args = parser.parse_args()
    
    # Create and run sync runner
    runner = SyncRunner(
        dry_run=args.dry_run,
        debug=args.debug,
        limit=args.limit
    )
    
    success = runner.run_sync(args.base_ref, args.target_ref)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()