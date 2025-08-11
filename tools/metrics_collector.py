"""Metrics collection for LLM translation pipeline."""

import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from threading import Lock


@dataclass
class FileMetrics:
    """Metrics for a single file."""
    path: str
    operation: str  # inserted, replaced, kept, deleted, nondoc_copied
    lines_before: int = 0
    lines_after: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    llm_calls: int = 0
    retries: int = 0
    processing_time: float = 0.0
    cache_hits: int = 0
    upstream_sha: str = ""
    strategy: str = ""
    error: Optional[str] = None


@dataclass
class PipelineMetrics:
    """Overall pipeline metrics."""
    start_time: datetime
    end_time: Optional[datetime] = None
    total_processing_time: float = 0.0
    files: List[FileMetrics] = None
    
    def __post_init__(self):
        if self.files is None:
            self.files = []


class MetricsCollector:
    """Collect and aggregate metrics for the translation pipeline."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.pipeline_metrics = PipelineMetrics(start_time=datetime.now())
        self._lock = Lock()
    
    def start_pipeline(self):
        """Mark pipeline start."""
        with self._lock:
            self.pipeline_metrics.start_time = datetime.now()
    
    def end_pipeline(self):
        """Mark pipeline end."""
        with self._lock:
            self.pipeline_metrics.end_time = datetime.now()
            if self.pipeline_metrics.start_time:
                delta = self.pipeline_metrics.end_time - self.pipeline_metrics.start_time
                self.pipeline_metrics.total_processing_time = delta.total_seconds()
    
    def add_file_metrics(self, file_metrics: FileMetrics):
        """Add metrics for a file."""
        with self._lock:
            self.pipeline_metrics.files.append(file_metrics)
    
    def record_file_operation(self, file_path: str, operation: str, 
                            lines_before: int = 0, lines_after: int = 0,
                            upstream_sha: str = "", strategy: str = "",
                            error: Optional[str] = None) -> FileMetrics:
        """Record a file operation and return the metrics object for further updates."""
        lines_added = max(0, lines_after - lines_before) if operation != "deleted" else 0
        lines_removed = max(0, lines_before - lines_after) if operation != "inserted" else 0
        
        file_metrics = FileMetrics(
            path=file_path,
            operation=operation,
            lines_before=lines_before,
            lines_after=lines_after,
            lines_added=lines_added,
            lines_removed=lines_removed,
            upstream_sha=upstream_sha,
            strategy=strategy,
            error=error
        )
        
        self.add_file_metrics(file_metrics)
        return file_metrics
    
    def record_llm_call(self, file_path: str, retry_count: int = 0, 
                       processing_time: float = 0.0, cache_hit: bool = False):
        """Record an LLM call for a file."""
        with self._lock:
            # Find the file metrics and update
            for file_metrics in self.pipeline_metrics.files:
                if file_metrics.path == file_path:
                    file_metrics.llm_calls += 1
                    file_metrics.retries += retry_count
                    file_metrics.processing_time += processing_time
                    if cache_hit:
                        file_metrics.cache_hits += 1
                    break
    
    def get_aggregated_statistics(self) -> Dict[str, Any]:
        """Get aggregated statistics."""
        with self._lock:
            files_by_operation = {"inserted": 0, "replaced": 0, "kept": 0, "deleted": 0, "nondoc_copied": 0}
            total_llm_calls = 0
            total_retries = 0
            total_cache_hits = 0
            total_lines_added = 0
            total_lines_removed = 0
            error_count = 0
            
            for file_metrics in self.pipeline_metrics.files:
                # Count files by operation
                if file_metrics.operation in files_by_operation:
                    files_by_operation[file_metrics.operation] += 1
                
                # Aggregate other metrics
                total_llm_calls += file_metrics.llm_calls
                total_retries += file_metrics.retries
                total_cache_hits += file_metrics.cache_hits
                total_lines_added += file_metrics.lines_added
                total_lines_removed += file_metrics.lines_removed
                
                if file_metrics.error:
                    error_count += 1
            
            return {
                "summary": {
                    "files": files_by_operation,
                    "operations": {
                        "llm_calls": total_llm_calls,
                        "retries": total_retries,
                        "cache_hits": total_cache_hits,
                        "total_processing_time": self.pipeline_metrics.total_processing_time,
                        "error_count": error_count
                    },
                    "lines": {
                        "added": total_lines_added,
                        "removed": total_lines_removed
                    }
                },
                "pipeline": {
                    "start_time": self.pipeline_metrics.start_time.isoformat() if self.pipeline_metrics.start_time else None,
                    "end_time": self.pipeline_metrics.end_time.isoformat() if self.pipeline_metrics.end_time else None,
                    "total_processing_time": self.pipeline_metrics.total_processing_time
                }
            }
    
    def get_detailed_file_metrics(self) -> List[Dict[str, Any]]:
        """Get detailed metrics for each file."""
        with self._lock:
            return [asdict(file_metrics) for file_metrics in self.pipeline_metrics.files]
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate complete report with all metrics."""
        return {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "pipeline_version": "1.0",
                "total_files": len(self.pipeline_metrics.files)
            },
            **self.get_aggregated_statistics(),
            "files": self.get_detailed_file_metrics()
        }
    
    def save_report(self, output_path: str) -> bool:
        """Save metrics report to JSON file."""
        try:
            report = self.generate_report()
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving metrics report: {e}")
            return False


# Global metrics collector instance
_metrics_collector = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def reset_metrics_collector():
    """Reset the global metrics collector (mainly for testing)."""
    global _metrics_collector
    _metrics_collector = None


if __name__ == "__main__":
    # Simple test
    collector = MetricsCollector()
    collector.start_pipeline()
    
    # Simulate some operations
    file1 = collector.record_file_operation("docs/test1.md", "replaced", 10, 12, "abc123", "retranslate")
    collector.record_llm_call("docs/test1.md", 0, 2.5)
    
    file2 = collector.record_file_operation("docs/test2.md", "inserted", 0, 5, "def456", "new")
    collector.record_llm_call("docs/test2.md", 1, 1.2)  # 1 retry
    
    collector.record_file_operation("static/image.png", "nondoc_copied", 0, 0, "ghi789", "copy")
    
    collector.end_pipeline()
    
    # Print report
    report = collector.generate_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))