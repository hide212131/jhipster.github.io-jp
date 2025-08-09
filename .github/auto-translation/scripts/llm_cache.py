#!/usr/bin/env python3
"""
JHipster日本語ドキュメント自動翻訳システム
LLMキャッシュシステム - SQLiteベース
"""

import sqlite3
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMCache:
    """SQLiteベースのLLMキャッシュシステム"""
    
    def __init__(self, cache_db_path: Optional[str] = None):
        """
        キャッシュシステムを初期化
        
        Args:
            cache_db_path: SQLiteデータベースファイルのパス。Noneの場合は.out/llm_cache.dbを使用
        """
        if cache_db_path is None:
            # プロジェクトルートを見つける
            current = Path(__file__).parent
            while current != current.parent:
                if (current / '.git').exists() or (current / 'package.json').exists():
                    project_root = current
                    break
                current = current.parent
            else:
                project_root = Path.cwd()
            
            # .outディレクトリを作成
            cache_dir = project_root / ".github" / "auto-translation" / ".out"
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_db_path = str(cache_dir / "llm_cache.db")
        
        self.db_path = cache_db_path
        self.init_database()
        
        # 統計情報
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_stores": 0
        }
    
    def init_database(self):
        """データベースとテーブルを初期化"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # キャッシュテーブル作成
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS translation_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    upstream_sha TEXT NOT NULL,
                    line_no INTEGER NOT NULL,
                    src_hash TEXT NOT NULL,
                    original_content TEXT NOT NULL,
                    translated_content TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 1,
                    UNIQUE(file_path, upstream_sha, line_no, src_hash)
                )
            """)
            
            # インデックス作成
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_lookup 
                ON translation_cache(file_path, upstream_sha, line_no, src_hash)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_accessed_at 
                ON translation_cache(accessed_at)
            """)
            
            conn.commit()
            logger.info(f"✅ Cache database initialized: {self.db_path}")
    
    def _generate_content_hash(self, content: str) -> str:
        """コンテンツのSHA256ハッシュを生成"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]  # 短縮版
    
    def get_cache_key(self, file_path: str, upstream_sha: str, line_no: int, content: str) -> Tuple[str, str, int, str]:
        """キャッシュキーを生成"""
        src_hash = self._generate_content_hash(content)
        return (file_path, upstream_sha, line_no, src_hash)
    
    def get(self, file_path: str, upstream_sha: str, line_no: int, content: str) -> Optional[str]:
        """
        キャッシュから翻訳結果を取得
        
        Args:
            file_path: ファイルパス
            upstream_sha: アップストリームコミットハッシュ
            line_no: 行番号
            content: 元のコンテンツ
            
        Returns:
            翻訳結果またはNone（キャッシュミスの場合）
        """
        file_path, upstream_sha, line_no, src_hash = self.get_cache_key(file_path, upstream_sha, line_no, content)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT translated_content, model_name, access_count
                    FROM translation_cache 
                    WHERE file_path = ? AND upstream_sha = ? AND line_no = ? AND src_hash = ?
                """, (file_path, upstream_sha, line_no, src_hash))
                
                result = cursor.fetchone()
                
                if result:
                    translated_content, model_name, access_count = result
                    
                    # アクセス情報を更新
                    cursor.execute("""
                        UPDATE translation_cache 
                        SET accessed_at = CURRENT_TIMESTAMP, access_count = access_count + 1
                        WHERE file_path = ? AND upstream_sha = ? AND line_no = ? AND src_hash = ?
                    """, (file_path, upstream_sha, line_no, src_hash))
                    
                    conn.commit()
                    
                    self.stats["cache_hits"] += 1
                    logger.debug(f"🎯 Cache HIT: {file_path}:{line_no} (model: {model_name}, access: {access_count + 1})")
                    return translated_content
                else:
                    self.stats["cache_misses"] += 1
                    logger.debug(f"❌ Cache MISS: {file_path}:{line_no}")
                    return None
                    
        except sqlite3.Error as e:
            logger.error(f"❌ Cache lookup error: {e}")
            self.stats["cache_misses"] += 1
            return None
    
    def put(self, file_path: str, upstream_sha: str, line_no: int, original_content: str, 
            translated_content: str, model_name: str = "gemini-1.5-flash") -> bool:
        """
        翻訳結果をキャッシュに保存
        
        Args:
            file_path: ファイルパス
            upstream_sha: アップストリームコミットハッシュ
            line_no: 行番号
            original_content: 元のコンテンツ
            translated_content: 翻訳結果
            model_name: 使用したモデル名
            
        Returns:
            保存成功した場合True
        """
        file_path, upstream_sha, line_no, src_hash = self.get_cache_key(file_path, upstream_sha, line_no, original_content)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # UPSERT (INSERT OR REPLACE)
                cursor.execute("""
                    INSERT OR REPLACE INTO translation_cache 
                    (file_path, upstream_sha, line_no, src_hash, original_content, translated_content, model_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (file_path, upstream_sha, line_no, src_hash, original_content, translated_content, model_name))
                
                conn.commit()
                
                self.stats["cache_stores"] += 1
                logger.debug(f"💾 Cache STORE: {file_path}:{line_no}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"❌ Cache store error: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """キャッシュ統計情報を取得"""
        total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        hit_rate = (self.stats["cache_hits"] / total_requests * 100) if total_requests > 0 else 0
        
        stats = self.stats.copy()
        stats.update({
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2)
        })
        
        return stats
    
    def get_database_stats(self) -> Dict:
        """データベース内の統計情報を取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 総エントリ数
                cursor.execute("SELECT COUNT(*) FROM translation_cache")
                total_entries = cursor.fetchone()[0]
                
                # ファイル別エントリ数
                cursor.execute("""
                    SELECT file_path, COUNT(*) as count 
                    FROM translation_cache 
                    GROUP BY file_path 
                    ORDER BY count DESC 
                    LIMIT 10
                """)
                top_files = cursor.fetchall()
                
                # 最新キャッシュエントリ
                cursor.execute("""
                    SELECT file_path, upstream_sha, created_at 
                    FROM translation_cache 
                    ORDER BY created_at DESC 
                    LIMIT 5
                """)
                recent_entries = cursor.fetchall()
                
                # データベースサイズ（概算）
                cursor.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0]
                cursor.execute("PRAGMA page_size")
                page_size = cursor.fetchone()[0]
                db_size_bytes = page_count * page_size
                
                return {
                    "total_entries": total_entries,
                    "top_files": [{"file": f, "count": c} for f, c in top_files],
                    "recent_entries": [{"file": f, "sha": s, "created": c} for f, s, c in recent_entries],
                    "database_size_mb": round(db_size_bytes / (1024 * 1024), 2)
                }
                
        except sqlite3.Error as e:
            logger.error(f"❌ Database stats error: {e}")
            return {"error": str(e)}
    
    def cleanup_old_entries(self, days_old: int = 30) -> int:
        """古いキャッシュエントリを削除"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM translation_cache 
                    WHERE accessed_at < datetime('now', '-{} days')
                """.format(days_old))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"🧹 Cleaned up {deleted_count} old cache entries (older than {days_old} days)")
                return deleted_count
                
        except sqlite3.Error as e:
            logger.error(f"❌ Cleanup error: {e}")
            return 0
    
    def clear_cache(self) -> bool:
        """全キャッシュを削除"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM translation_cache")
                conn.commit()
                
                logger.info("🧹 Cache cleared completely")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"❌ Cache clear error: {e}")
            return False


def main():
    """CLI テスト用メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM Cache Management")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # stats コマンド
    stats_parser = subparsers.add_parser('stats', help='Show cache statistics')
    
    # cleanup コマンド
    cleanup_parser = subparsers.add_parser('cleanup', help='Cleanup old cache entries')
    cleanup_parser.add_argument('--days', type=int, default=30, help='Days to keep (default: 30)')
    
    # clear コマンド
    clear_parser = subparsers.add_parser('clear', help='Clear all cache')
    
    args = parser.parse_args()
    
    cache = LLMCache()
    
    if args.command == 'stats':
        runtime_stats = cache.get_stats()
        db_stats = cache.get_database_stats()
        
        print("=== Runtime Statistics ===")
        print(json.dumps(runtime_stats, indent=2))
        print("\n=== Database Statistics ===")
        print(json.dumps(db_stats, indent=2))
        
    elif args.command == 'cleanup':
        deleted = cache.cleanup_old_entries(args.days)
        print(f"Deleted {deleted} old entries")
        
    elif args.command == 'clear':
        if cache.clear_cache():
            print("Cache cleared successfully")
        else:
            print("Failed to clear cache")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()