"""
SQLite-based translation cache for JP translation tools.

Provides caching functionality with schema: (path, upstream_sha, line_no, src_hash, translation_result, timestamp)
to improve translation performance and enable observability.
"""

import sqlite3
import hashlib
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path


class TranslationCache:
    """SQLite-based cache for translation results."""
    
    def __init__(self, cache_dir: str = ".cache"):
        """Initialize the cache with SQLite database.
        
        Args:
            cache_dir: Directory to store the cache database
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.db_path = self.cache_dir / "translation_cache.db"
        self._init_database()
        
    def _init_database(self):
        """Initialize the SQLite database with required schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS translation_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT NOT NULL,
                    upstream_sha TEXT NOT NULL,
                    line_no INTEGER NOT NULL,
                    src_hash TEXT NOT NULL,
                    translation_result TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    UNIQUE(path, upstream_sha, line_no, src_hash)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_lookup 
                ON translation_cache(path, upstream_sha, line_no, src_hash)
            """)
            conn.commit()
    
    def _calculate_hash(self, content: str) -> str:
        """Calculate SHA256 hash of content.
        
        Args:
            content: Source content to hash
            
        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def get(self, path: str, upstream_sha: str, line_no: int, src_content: str) -> Optional[str]:
        """Get cached translation result.
        
        Args:
            path: File path
            upstream_sha: Git SHA of upstream version
            line_no: Line number
            src_content: Source content to translate
            
        Returns:
            Cached translation result if found, None otherwise
        """
        src_hash = self._calculate_hash(src_content)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT translation_result FROM translation_cache WHERE path=? AND upstream_sha=? AND line_no=? AND src_hash=?",
                (path, upstream_sha, line_no, src_hash)
            )
            result = cursor.fetchone()
            return result[0] if result else None
    
    def set(self, path: str, upstream_sha: str, line_no: int, src_content: str, translation: str) -> None:
        """Store translation result in cache.
        
        Args:
            path: File path
            upstream_sha: Git SHA of upstream version
            line_no: Line number
            src_content: Source content
            translation: Translation result
        """
        src_hash = self._calculate_hash(src_content)
        timestamp = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO translation_cache 
                (path, upstream_sha, line_no, src_hash, translation_result, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (path, upstream_sha, line_no, src_hash, translation, timestamp))
            conn.commit()
    
    def exists(self, path: str, upstream_sha: str, line_no: int, src_content: str) -> bool:
        """Check if translation exists in cache.
        
        Args:
            path: File path
            upstream_sha: Git SHA of upstream version
            line_no: Line number
            src_content: Source content
            
        Returns:
            True if cached translation exists
        """
        return self.get(path, upstream_sha, line_no, src_content) is not None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM translation_cache")
            total_entries = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(DISTINCT path) FROM translation_cache")
            unique_files = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM translation_cache")
            date_range = cursor.fetchone()
            
            return {
                "total_entries": total_entries,
                "unique_files": unique_files,
                "first_entry": date_range[0],
                "last_entry": date_range[1],
                "database_size_bytes": os.path.getsize(self.db_path) if self.db_path.exists() else 0
            }
    
    def get_entries_for_file(self, path: str, upstream_sha: str) -> List[Tuple[int, str, str, str]]:
        """Get all cached entries for a specific file.
        
        Args:
            path: File path
            upstream_sha: Git SHA of upstream version
            
        Returns:
            List of tuples: (line_no, src_hash, translation_result, timestamp)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT line_no, src_hash, translation_result, timestamp 
                FROM translation_cache 
                WHERE path=? AND upstream_sha=?
                ORDER BY line_no
            """, (path, upstream_sha))
            return cursor.fetchall()
    
    def clear_cache(self, path: Optional[str] = None) -> int:
        """Clear cache entries.
        
        Args:
            path: If specified, only clear entries for this path
            
        Returns:
            Number of entries deleted
        """
        with sqlite3.connect(self.db_path) as conn:
            if path:
                cursor = conn.execute("DELETE FROM translation_cache WHERE path=?", (path,))
            else:
                cursor = conn.execute("DELETE FROM translation_cache")
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count


class CacheSession:
    """Session to track cache hit/miss rates during a translation run."""
    
    def __init__(self, cache: TranslationCache):
        """Initialize cache session.
        
        Args:
            cache: TranslationCache instance
        """
        self.cache = cache
        self.hits = 0
        self.misses = 0
        self.operations = []
        
    def lookup(self, path: str, upstream_sha: str, line_no: int, src_content: str) -> Optional[str]:
        """Lookup with hit/miss tracking.
        
        Args:
            path: File path
            upstream_sha: Git SHA of upstream version
            line_no: Line number
            src_content: Source content
            
        Returns:
            Cached translation if found, None otherwise
        """
        result = self.cache.get(path, upstream_sha, line_no, src_content)
        operation = {
            "path": path,
            "upstream_sha": upstream_sha,
            "line_no": line_no,
            "hit": result is not None,
            "timestamp": datetime.now().isoformat()
        }
        
        if result is not None:
            self.hits += 1
            operation["result"] = "hit"
        else:
            self.misses += 1
            operation["result"] = "miss"
            
        self.operations.append(operation)
        return result
    
    def store(self, path: str, upstream_sha: str, line_no: int, src_content: str, translation: str) -> None:
        """Store translation with tracking.
        
        Args:
            path: File path
            upstream_sha: Git SHA of upstream version
            line_no: Line number
            src_content: Source content
            translation: Translation result
        """
        self.cache.set(path, upstream_sha, line_no, src_content, translation)
        
    def get_hit_rate(self) -> float:
        """Get cache hit rate for this session.
        
        Returns:
            Hit rate as percentage (0.0 to 100.0)
        """
        total = self.hits + self.misses
        return (self.hits / total * 100.0) if total > 0 else 0.0
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics for this session.
        
        Returns:
            Dictionary with session statistics
        """
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_operations": self.hits + self.misses,
            "hit_rate": self.get_hit_rate(),
            "operations": self.operations
        }