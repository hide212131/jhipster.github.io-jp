"""SQLite-based translation cache for LLM results."""

import sqlite3
import hashlib
import json
import time
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from datetime import datetime, timedelta


class TranslationCache:
    """SQLite-based cache for translation results."""
    
    def __init__(self, cache_dir: Path = None):
        """Initialize translation cache.
        
        Args:
            cache_dir: Directory for cache database. Defaults to tools/.cache
        """
        if cache_dir is None:
            cache_dir = Path(__file__).parent / ".cache"
        
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = cache_dir / "translation_cache.db"
        self.call_count = 0
        self.hit_count = 0
        self.miss_count = 0
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS translations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_hash TEXT UNIQUE NOT NULL,
                    source_text TEXT NOT NULL,
                    context_hash TEXT,
                    context_text TEXT,
                    target_text TEXT NOT NULL,
                    model_name TEXT,
                    model_version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 1
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_source_hash 
                ON translations (source_hash)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_context_hash 
                ON translations (context_hash)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON translations (created_at)
            """)
    
    def _generate_hash(self, text: str) -> str:
        """Generate hash for text content."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def _generate_cache_key(self, source_text: str, context: str = "", 
                           model_name: str = "gemini", model_version: str = "1.0") -> Tuple[str, str]:
        """Generate cache keys for source and context.
        
        Returns:
            Tuple of (source_hash, context_hash)
        """
        source_hash = self._generate_hash(f"{source_text}:{model_name}:{model_version}")
        context_hash = self._generate_hash(context) if context else ""
        return source_hash, context_hash
    
    def get(self, source_text: str, context: str = "", 
            model_name: str = "gemini", model_version: str = "1.0") -> Optional[str]:
        """Get cached translation if exists.
        
        Args:
            source_text: Text to translate
            context: Translation context
            model_name: Model name for cache key
            model_version: Model version for cache key
            
        Returns:
            Cached translation or None if not found
        """
        source_hash, context_hash = self._generate_cache_key(
            source_text, context, model_name, model_version
        )
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT target_text FROM translations 
                WHERE source_hash = ? AND context_hash = ?
            """, (source_hash, context_hash))
            
            result = cursor.fetchone()
            
            if result:
                # Update access statistics
                conn.execute("""
                    UPDATE translations 
                    SET last_accessed = CURRENT_TIMESTAMP, 
                        access_count = access_count + 1
                    WHERE source_hash = ? AND context_hash = ?
                """, (source_hash, context_hash))
                
                self.hit_count += 1
                return result[0]
            else:
                self.miss_count += 1
                return None
    
    def put(self, source_text: str, target_text: str, context: str = "",
            model_name: str = "gemini", model_version: str = "1.0"):
        """Store translation in cache.
        
        Args:
            source_text: Original text
            target_text: Translated text
            context: Translation context
            model_name: Model name for cache key
            model_version: Model version for cache key
        """
        source_hash, context_hash = self._generate_cache_key(
            source_text, context, model_name, model_version
        )
        
        with sqlite3.connect(self.db_path) as conn:
            # Use INSERT OR REPLACE to handle duplicates
            conn.execute("""
                INSERT OR REPLACE INTO translations 
                (source_hash, source_text, context_hash, context_text, 
                 target_text, model_name, model_version)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (source_hash, source_text, context_hash, context, 
                  target_text, model_name, model_version))
    
    def batch_get(self, texts_with_context: List[Tuple[str, str]], 
                  model_name: str = "gemini", model_version: str = "1.0") -> List[Optional[str]]:
        """Get multiple cached translations.
        
        Args:
            texts_with_context: List of (source_text, context) tuples
            model_name: Model name for cache key
            model_version: Model version for cache key
            
        Returns:
            List of cached translations (None for cache misses)
        """
        if not texts_with_context:
            return []
        
        # Generate all cache keys
        cache_keys = []
        for source_text, context in texts_with_context:
            source_hash, context_hash = self._generate_cache_key(
                source_text, context, model_name, model_version
            )
            cache_keys.append((source_hash, context_hash))
        
        # Query all keys at once
        placeholders = ",".join(["(?,?)"] * len(cache_keys))
        query = f"""
            SELECT source_hash, context_hash, target_text 
            FROM translations 
            WHERE (source_hash, context_hash) IN ({placeholders})
        """
        
        # Flatten cache keys for query parameters
        query_params = []
        for source_hash, context_hash in cache_keys:
            query_params.extend([source_hash, context_hash])
        
        results = {}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, query_params)
            
            for row in cursor.fetchall():
                source_hash, context_hash, target_text = row
                results[(source_hash, context_hash)] = target_text
                
                # Update access statistics
                conn.execute("""
                    UPDATE translations 
                    SET last_accessed = CURRENT_TIMESTAMP, 
                        access_count = access_count + 1
                    WHERE source_hash = ? AND context_hash = ?
                """, (source_hash, context_hash))
        
        # Build result list in original order
        translations = []
        for i, (source_hash, context_hash) in enumerate(cache_keys):
            if (source_hash, context_hash) in results:
                translations.append(results[(source_hash, context_hash)])
                self.hit_count += 1
            else:
                translations.append(None)
                self.miss_count += 1
        
        return translations
    
    def batch_put(self, translations: List[Tuple[str, str, str]], 
                  model_name: str = "gemini", model_version: str = "1.0"):
        """Store multiple translations in cache.
        
        Args:
            translations: List of (source_text, target_text, context) tuples
            model_name: Model name for cache key
            model_version: Model version for cache key
        """
        if not translations:
            return
        
        records = []
        for source_text, target_text, context in translations:
            source_hash, context_hash = self._generate_cache_key(
                source_text, context, model_name, model_version
            )
            records.append((
                source_hash, source_text, context_hash, context,
                target_text, model_name, model_version
            ))
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany("""
                INSERT OR REPLACE INTO translations 
                (source_hash, source_text, context_hash, context_text, 
                 target_text, model_name, model_version)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, records)
    
    def clear_old_entries(self, days: int = 30):
        """Clear cache entries older than specified days.
        
        Args:
            days: Number of days to keep entries
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM translations 
                WHERE last_accessed < ?
            """, (cutoff_date.isoformat(),))
            
            deleted_count = cursor.rowcount
            return deleted_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_entries,
                    SUM(access_count) as total_accesses,
                    AVG(access_count) as avg_accesses,
                    MIN(created_at) as oldest_entry,
                    MAX(created_at) as newest_entry
                FROM translations
            """)
            
            row = cursor.fetchone()
            if row:
                stats = {
                    "total_entries": row[0] or 0,
                    "total_accesses": row[1] or 0,
                    "avg_accesses": row[2] or 0,
                    "oldest_entry": row[3],
                    "newest_entry": row[4],
                    "session_hits": self.hit_count,
                    "session_misses": self.miss_count,
                    "session_total": self.hit_count + self.miss_count,
                }
                
                if stats["session_total"] > 0:
                    stats["session_hit_rate"] = self.hit_count / stats["session_total"]
                else:
                    stats["session_hit_rate"] = 0.0
                
                return stats
        
        return {
            "total_entries": 0,
            "total_accesses": 0,
            "avg_accesses": 0,
            "oldest_entry": None,
            "newest_entry": None,
            "session_hits": self.hit_count,
            "session_misses": self.miss_count,
            "session_total": self.hit_count + self.miss_count,
            "session_hit_rate": 0.0
        }
    
    def close(self):
        """Close cache connection (no-op for SQLite)."""
        # SQLite connections are closed automatically
        pass