"""
Report generation for translation tools.

Generates tools/.out/report.json with line-by-line reasoning and cache statistics.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    from .cache import TranslationCache, CacheSession
except ImportError:
    from cache import TranslationCache, CacheSession


class TranslationReporter:
    """Generate reports for translation operations."""
    
    def __init__(self, output_dir: str = "tools/.out"):
        """Initialize reporter.
        
        Args:
            output_dir: Directory to write reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.report_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "version": "1.0.0"
            },
            "cache_stats": {},
            "files": {},
            "session_stats": {},
            "line_decisions": []
        }
        
    def add_cache_stats(self, cache: TranslationCache) -> None:
        """Add cache statistics to report.
        
        Args:
            cache: TranslationCache instance
        """
        self.report_data["cache_stats"] = cache.get_stats()
        
    def add_session_stats(self, session: CacheSession) -> None:
        """Add session statistics to report.
        
        Args:
            session: CacheSession instance
        """
        self.report_data["session_stats"] = session.get_session_stats()
        
    def add_file_processing(self, path: str, upstream_sha: str, total_lines: int, 
                           processed_lines: int, cache_hits: int) -> None:
        """Add file processing information.
        
        Args:
            path: File path
            upstream_sha: Git SHA of upstream version
            total_lines: Total lines in file
            processed_lines: Number of lines processed
            cache_hits: Number of cache hits for this file
        """
        self.report_data["files"][path] = {
            "upstream_sha": upstream_sha,
            "total_lines": total_lines,
            "processed_lines": processed_lines,
            "cache_hits": cache_hits,
            "cache_hit_rate": (cache_hits / processed_lines * 100.0) if processed_lines > 0 else 0.0,
            "processed_at": datetime.now().isoformat()
        }
        
    def add_line_decision(self, path: str, line_no: int, src_content: str, 
                         translation: str, decision_reason: str, 
                         was_cached: bool = False, processing_time_ms: float = 0.0) -> None:
        """Add line-by-line decision reasoning.
        
        Args:
            path: File path
            line_no: Line number
            src_content: Original source content
            translation: Translation result
            decision_reason: Reason for translation decision
            was_cached: Whether result came from cache
            processing_time_ms: Processing time in milliseconds
        """
        decision = {
            "path": path,
            "line_no": line_no,
            "src_content": src_content[:100] + "..." if len(src_content) > 100 else src_content,
            "translation": translation[:100] + "..." if len(translation) > 100 else translation,
            "decision_reason": decision_reason,
            "was_cached": was_cached,
            "processing_time_ms": processing_time_ms,
            "timestamp": datetime.now().isoformat()
        }
        self.report_data["line_decisions"].append(decision)
        
    def add_summary_stats(self, total_files: int, total_lines: int, 
                         total_translations: int, total_cache_hits: int,
                         total_processing_time_ms: float) -> None:
        """Add summary statistics.
        
        Args:
            total_files: Total number of files processed
            total_lines: Total number of lines processed
            total_translations: Total number of translations performed
            total_cache_hits: Total cache hits across all operations
            total_processing_time_ms: Total processing time in milliseconds
        """
        self.report_data["summary"] = {
            "total_files": total_files,
            "total_lines": total_lines,
            "total_translations": total_translations,
            "total_cache_hits": total_cache_hits,
            "overall_cache_hit_rate": (total_cache_hits / total_translations * 100.0) if total_translations > 0 else 0.0,
            "total_processing_time_ms": total_processing_time_ms,
            "avg_processing_time_per_line_ms": (total_processing_time_ms / total_lines) if total_lines > 0 else 0.0
        }
        
    def generate_report(self) -> str:
        """Generate and save the report.
        
        Returns:
            Path to the generated report file
        """
        report_path = self.output_dir / "report.json"
        
        # Sort line decisions by path and line number for readability
        self.report_data["line_decisions"].sort(key=lambda x: (x["path"], x["line_no"]))
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.report_data, f, indent=2, ensure_ascii=False)
            
        return str(report_path)
    
    def get_report_data(self) -> Dict[str, Any]:
        """Get current report data.
        
        Returns:
            Report data dictionary
        """
        return self.report_data.copy()


def create_demo_report(cache: TranslationCache, output_dir: str = "tools/.out") -> str:
    """Create a demonstration report with sample data.
    
    Args:
        cache: TranslationCache instance
        output_dir: Output directory for report
        
    Returns:
        Path to generated report
    """
    reporter = TranslationReporter(output_dir)
    
    # Add cache statistics
    reporter.add_cache_stats(cache)
    
    # Simulate some file processing
    sample_files = [
        ("pages/getting-started.md", "abc123", 50, 45, 12),
        ("pages/installation.md", "def456", 30, 28, 8),
        ("_posts/2023-01-01-news.md", "ghi789", 25, 20, 5)
    ]
    
    for path, sha, total, processed, hits in sample_files:
        reporter.add_file_processing(path, sha, total, processed, hits)
    
    # Simulate line decisions
    sample_decisions = [
        ("pages/getting-started.md", 1, "# Getting Started", "# 始めよう", "Header translation using standard pattern", False, 120.5),
        ("pages/getting-started.md", 2, "Welcome to our application", "私たちのアプリケーションへようこそ", "Formal welcome message", True, 2.1),
        ("pages/installation.md", 1, "Installation guide", "インストールガイド", "Direct translation of technical term", False, 89.3),
        ("pages/installation.md", 5, "Run the following command:", "次のコマンドを実行してください：", "Instruction translation with formal tone", True, 1.8)
    ]
    
    for path, line_no, src, translation, reason, cached, time_ms in sample_decisions:
        reporter.add_line_decision(path, line_no, src, translation, reason, cached, time_ms)
    
    # Add summary
    reporter.add_summary_stats(
        total_files=3,
        total_lines=93,
        total_translations=93,
        total_cache_hits=25,
        total_processing_time_ms=1250.7
    )
    
    return reporter.generate_report()