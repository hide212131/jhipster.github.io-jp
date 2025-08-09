#!/usr/bin/env python3
"""
Demo CLI for translation cache and reporting system.

Demonstrates cache hit rate improvement and report generation.
"""

import sys
import time
from pathlib import Path

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent))

from cache import TranslationCache, CacheSession
from report import TranslationReporter, create_demo_report


def simulate_translation(text: str, delay: float = 0.1) -> str:
    """Simulate translation with artificial delay.
    
    Args:
        text: Text to translate
        delay: Artificial delay in seconds
        
    Returns:
        Mock translation
    """
    time.sleep(delay)  # Simulate translation API call
    
    # Simple mock translations for demo
    translations = {
        "Getting Started": "始めよう",
        "Installation": "インストール", 
        "Welcome": "ようこそ",
        "Configuration": "設定",
        "Documentation": "ドキュメント",
        "Hello World": "こんにちは世界",
        "Tutorial": "チュートリアル",
        "Examples": "例"
    }
    
    return translations.get(text, f"[翻訳: {text}]")


def demo_cache_performance():
    """Demonstrate cache performance improvement."""
    print("Translation Cache Demo")
    print("=" * 50)
    
    # Initialize cache
    cache = TranslationCache()
    
    # Sample content to translate
    sample_content = [
        ("pages/getting-started.md", "abc123", 1, "Getting Started"),
        ("pages/getting-started.md", "abc123", 2, "Welcome"),
        ("pages/installation.md", "def456", 1, "Installation"),
        ("pages/installation.md", "def456", 2, "Configuration"),
        ("pages/docs.md", "ghi789", 1, "Documentation"),
        ("pages/tutorial.md", "jkl012", 1, "Tutorial"),
        ("pages/examples.md", "mno345", 1, "Examples"),
        ("pages/hello.md", "pqr678", 1, "Hello World"),
    ]
    
    print("\n🚀 First run (no cache):")
    session1 = CacheSession(cache)
    start_time = time.time()
    
    for path, sha, line_no, content in sample_content:
        # Try cache first
        cached_result = session1.lookup(path, sha, line_no, content)
        
        if cached_result is None:
            # Simulate translation
            translation = simulate_translation(content)
            session1.store(path, sha, line_no, content, translation)
            print(f"  ⏱️  Translated '{content}' -> '{translation}'")
        else:
            print(f"  ⚡ Cache hit: '{content}' -> '{cached_result}'")
    
    first_run_time = time.time() - start_time
    print(f"\n📊 First run stats:")
    print(f"   Hit rate: {session1.get_hit_rate():.1f}%")
    print(f"   Time: {first_run_time:.2f}s")
    
    print("\n🔄 Second run (with cache):")
    session2 = CacheSession(cache)
    start_time = time.time()
    
    for path, sha, line_no, content in sample_content:
        # Try cache first
        cached_result = session2.lookup(path, sha, line_no, content)
        
        if cached_result is None:
            # Simulate translation
            translation = simulate_translation(content)
            session2.store(path, sha, line_no, content, translation)
            print(f"  ⏱️  Translated '{content}' -> '{translation}'")
        else:
            print(f"  ⚡ Cache hit: '{content}' -> '{cached_result}'")
    
    second_run_time = time.time() - start_time
    print(f"\n📊 Second run stats:")
    print(f"   Hit rate: {session2.get_hit_rate():.1f}%")
    print(f"   Time: {second_run_time:.2f}s")
    print(f"   Speed improvement: {(first_run_time / second_run_time):.1f}x faster")
    
    # Generate report
    print(f"\n📋 Generating report...")
    reporter = TranslationReporter()
    reporter.add_cache_stats(cache)
    reporter.add_session_stats(session2)
    
    # Add some line decisions
    for i, (path, sha, line_no, content) in enumerate(sample_content):
        translation = simulate_translation(content, delay=0)  # No delay for report
        was_cached = i < len(sample_content)  # All were cached in second run
        reporter.add_line_decision(
            path, line_no, content, translation,
            f"Standard translation using cache lookup" if was_cached else "Fresh translation",
            was_cached, 2.0 if was_cached else 100.0
        )
    
    reporter.add_summary_stats(
        total_files=len(set(item[0] for item in sample_content)),
        total_lines=len(sample_content),
        total_translations=len(sample_content),
        total_cache_hits=session2.hits,
        total_processing_time_ms=second_run_time * 1000
    )
    
    report_path = reporter.generate_report()
    print(f"   Report saved to: {report_path}")
    
    # Display cache stats
    stats = cache.get_stats()
    print(f"\n💾 Cache statistics:")
    print(f"   Total entries: {stats['total_entries']}")
    print(f"   Unique files: {stats['unique_files']}")
    print(f"   Database size: {stats['database_size_bytes']} bytes")
    
    return cache


if __name__ == "__main__":
    cache = demo_cache_performance()
    
    print(f"\n🎯 Creating additional demo report...")
    demo_report_path = create_demo_report(cache)
    print(f"   Demo report saved to: {demo_report_path}")
    
    print(f"\n✅ Demo completed! Cache and reporting system is working.")