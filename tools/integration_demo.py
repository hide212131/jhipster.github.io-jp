"""
Integration example showing how cache and reporting work with line-lock and diff-engine.

This demonstrates the integration points for the translation pipeline.
"""

import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any
import time

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent))

from cache import TranslationCache, CacheSession
from report import TranslationReporter


class MockLineLock:
    """Mock line-lock functionality for demonstration."""
    
    def __init__(self):
        self.locked_lines = set()
    
    def is_locked(self, path: str, line_no: int) -> bool:
        """Check if a line is locked for editing."""
        return (path, line_no) in self.locked_lines
    
    def lock_line(self, path: str, line_no: int) -> bool:
        """Lock a line for editing."""
        if not self.is_locked(path, line_no):
            self.locked_lines.add((path, line_no))
            return True
        return False
    
    def unlock_line(self, path: str, line_no: int) -> None:
        """Unlock a line."""
        self.locked_lines.discard((path, line_no))


class MockDiffEngine:
    """Mock diff-engine functionality for demonstration."""
    
    def __init__(self):
        self.file_shas = {
            "pages/getting-started.md": "abc123",
            "pages/installation.md": "def456", 
            "pages/docs.md": "ghi789"
        }
    
    def get_upstream_sha(self, path: str) -> str:
        """Get upstream SHA for a file."""
        return self.file_shas.get(path, "unknown")
    
    def get_changed_lines(self, path: str) -> List[int]:
        """Get list of changed line numbers since last sync."""
        # Mock: return some changed lines
        return [1, 3, 5, 8] if "getting-started" in path else [2, 4]


class TranslationPipeline:
    """Integrated translation pipeline with caching, line-locking, and diff tracking."""
    
    def __init__(self, cache_dir: str = ".cache"):
        self.cache = TranslationCache(cache_dir)
        self.line_lock = MockLineLock()
        self.diff_engine = MockDiffEngine()
        self.reporter = TranslationReporter()
        
    def translate_text(self, text: str) -> str:
        """Mock translation function."""
        time.sleep(0.05)  # Simulate API call
        translations = {
            "Getting Started": "始めよう",
            "Installation Guide": "インストールガイド",
            "Welcome to our documentation": "私たちのドキュメントへようこそ",
            "Configuration": "設定",
            "Advanced Setup": "高度なセットアップ"
        }
        return translations.get(text, f"[翻訳: {text}]")
    
    def process_file(self, path: str, lines: List[str]) -> Dict[str, Any]:
        """Process a file with integrated caching, locking, and reporting."""
        print(f"\n📄 Processing file: {path}")
        
        session = CacheSession(self.cache)
        upstream_sha = self.diff_engine.get_upstream_sha(path)
        changed_lines = self.diff_engine.get_changed_lines(path)
        
        results = {
            "path": path,
            "upstream_sha": upstream_sha,
            "total_lines": len(lines),
            "processed": 0,
            "cached": 0,
            "locked": 0,
            "translations": {}
        }
        
        for line_no, content in enumerate(lines, 1):
            # Skip empty lines
            if not content.strip():
                continue
                
            # Check if line is locked
            if self.line_lock.is_locked(path, line_no):
                print(f"  🔒 Line {line_no}: Locked, skipping")
                results["locked"] += 1
                self.reporter.add_line_decision(
                    path, line_no, content, "", "Line is locked for editing", 
                    False, 0.0
                )
                continue
            
            # Try cache first
            start_time = time.time()
            cached_translation = session.lookup(path, upstream_sha, line_no, content)
            
            if cached_translation is not None:
                # Cache hit
                processing_time = (time.time() - start_time) * 1000
                print(f"  ⚡ Line {line_no}: Cache hit - '{content[:30]}...' -> '{cached_translation[:30]}...'")
                results["cached"] += 1
                results["translations"][line_no] = cached_translation
                
                self.reporter.add_line_decision(
                    path, line_no, content, cached_translation,
                    "Retrieved from cache", True, processing_time
                )
            else:
                # Cache miss - need to translate
                if line_no in changed_lines:
                    # Lock line for translation
                    if self.line_lock.lock_line(path, line_no):
                        try:
                            translation = self.translate_text(content)
                            processing_time = (time.time() - start_time) * 1000
                            
                            # Store in cache
                            session.store(path, upstream_sha, line_no, content, translation)
                            
                            print(f"  🔄 Line {line_no}: Translated - '{content[:30]}...' -> '{translation[:30]}...'")
                            results["translations"][line_no] = translation
                            
                            self.reporter.add_line_decision(
                                path, line_no, content, translation,
                                f"Fresh translation (line changed in diff)", False, processing_time
                            )
                        finally:
                            self.line_lock.unlock_line(path, line_no)
                    else:
                        print(f"  ⏸️  Line {line_no}: Could not acquire lock, skipping")
                        continue
                else:
                    print(f"  ⏭️  Line {line_no}: No changes detected, skipping")
                    continue
            
            results["processed"] += 1
        
        # Add file processing stats to report
        self.reporter.add_file_processing(
            path, upstream_sha, results["total_lines"], 
            results["processed"], results["cached"]
        )
        
        hit_rate = session.get_hit_rate()
        print(f"  📊 File stats: {results['processed']} processed, {results['cached']} cached ({hit_rate:.1f}% hit rate)")
        
        return results
    
    def run_translation_batch(self, files: Dict[str, List[str]]) -> str:
        """Run a batch of file translations."""
        print("🚀 Starting translation batch with integrated pipeline")
        print("=" * 60)
        
        batch_stats = {
            "total_files": 0,
            "total_lines": 0,
            "total_processed": 0,
            "total_cached": 0,
            "start_time": time.time()
        }
        
        for path, lines in files.items():
            result = self.process_file(path, lines)
            batch_stats["total_files"] += 1
            batch_stats["total_lines"] += result["total_lines"]
            batch_stats["total_processed"] += result["processed"]
            batch_stats["total_cached"] += result["cached"]
        
        processing_time = (time.time() - batch_stats["start_time"]) * 1000
        
        # Add summary to report
        self.reporter.add_summary_stats(
            batch_stats["total_files"],
            batch_stats["total_lines"], 
            batch_stats["total_processed"],
            batch_stats["total_cached"],
            processing_time
        )
        
        # Generate final report
        report_path = self.reporter.generate_report()
        
        print(f"\n📈 Batch Summary:")
        print(f"   Files processed: {batch_stats['total_files']}")
        print(f"   Lines processed: {batch_stats['total_processed']}/{batch_stats['total_lines']}")
        print(f"   Cache hits: {batch_stats['total_cached']}")
        if batch_stats['total_processed'] > 0:
            overall_hit_rate = batch_stats['total_cached'] / batch_stats['total_processed'] * 100
            print(f"   Overall hit rate: {overall_hit_rate:.1f}%")
        print(f"   Total time: {processing_time:.1f}ms")
        print(f"   Report saved: {report_path}")
        
        return report_path


def demo_integration():
    """Demonstrate the integrated translation pipeline."""
    
    # Sample files with content
    sample_files = {
        "pages/getting-started.md": [
            "Getting Started",
            "Welcome to our documentation", 
            "Installation Guide",
            "Configuration",
            "Advanced Setup"
        ],
        "pages/installation.md": [
            "Installation Guide",
            "Prerequisites", 
            "Download and Install",
            "Configuration"
        ]
    }
    
    # Create pipeline
    pipeline = TranslationPipeline()
    
    # Simulate some lines being locked
    pipeline.line_lock.lock_line("pages/getting-started.md", 2)
    
    # Run first batch
    print("First run (building cache):")
    report1 = pipeline.run_translation_batch(sample_files)
    
    print(f"\n" + "="*60)
    print("Second run (with cache):")
    
    # Create new pipeline instance to simulate fresh session
    pipeline2 = TranslationPipeline()
    report2 = pipeline2.run_translation_batch(sample_files)
    
    return report1, report2


if __name__ == "__main__":
    demo_integration()