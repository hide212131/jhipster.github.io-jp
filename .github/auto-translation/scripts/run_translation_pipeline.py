#!/usr/bin/env python3
"""
JHipster日本語ドキュメント自動翻訳システム
統合翻訳パイプライン実行スクリプト
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class TranslationPipeline:
    def __init__(self, commit_hash: str, dry_run: bool = False, mode: str = "normal",
                 before_commit: Optional[str] = None, limit: Optional[int] = None, 
                 paths: Optional[List[str]] = None):
        self.commit_hash = commit_hash
        self.dry_run = dry_run
        self.mode = mode
        self.before_commit = before_commit
        self.limit = limit
        self.paths = paths if paths else []
        self.start_time = datetime.now()
        self.script_dir = Path(__file__).parent
        self.classification_file = self.script_dir.parent / "classification.json"
        
        print(f"🚀 Translation Pipeline Starting")
        print(f"   Target commit: {commit_hash}")
        print(f"   Mode: {mode}")
        print(f"   Dry run: {dry_run}")
        if mode == "dev":
            if before_commit:
                print(f"   Before commit: {before_commit}")
            if limit:
                print(f"   File limit: {limit}")
            if paths:
                print(f"   Target paths: {', '.join(paths)}")
        print(f"   Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    def run_step(self, step_name: str, command: List[str], required: bool = True, 
                 env_vars: Optional[Dict[str, str]] = None) -> bool:
        """ステップを実行"""
        print(f"🔄 Step: {step_name}")
        print(f"   Command: {' '.join(command)}")
        
        if self.dry_run and step_name not in ["Fetch upstream", "Classify changes"]:
            print(f"   ⏭️  Skipped (dry run)")
            return True
        
        try:
            # 環境変数を設定
            env = os.environ.copy()
            if env_vars:
                env.update(env_vars)
            if self.dry_run:
                env["DRY_RUN"] = "true"
            
            start_time = time.time()
            result = subprocess.run(
                command, 
                check=True, 
                capture_output=True, 
                text=True,
                env=env,
                cwd=self.script_dir.parent
            )
            duration = time.time() - start_time
            
            print(f"   ✅ Completed in {duration:.1f}s")
            
            # 出力がある場合は表示（最後の数行のみ）
            if result.stdout.strip():
                output_lines = result.stdout.strip().split('\n')
                if len(output_lines) > 5:
                    print(f"   Output (last 5 lines):")
                    for line in output_lines[-5:]:
                        print(f"      {line}")
                else:
                    print(f"   Output:")
                    for line in output_lines:
                        print(f"      {line}")
            
            print()
            return True
            
        except subprocess.CalledProcessError as e:
            duration = time.time() - start_time
            print(f"   ❌ Failed in {duration:.1f}s")
            print(f"   Error: {e}")
            
            if e.stdout:
                print(f"   Stdout: {e.stdout}")
            if e.stderr:
                print(f"   Stderr: {e.stderr}")
                
            print()
            
            if required:
                print(f"💥 Pipeline failed at step: {step_name}")
                self.print_summary(success=False)
                sys.exit(1)
            return False

    def check_prerequisites(self) -> bool:
        """前提条件をチェック"""
        print("🔍 Checking prerequisites...")
        
        # API keys check
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "fake_api_key_for_development":
            print("   ⚠️  GEMINI_API_KEY not set or is placeholder")
            if not self.dry_run:
                print("   ❌ GEMINI_API_KEY is required for translation")
                return False
        else:
            print("   ✅ GEMINI_API_KEY is set")
        
        # Git config check
        try:
            subprocess.run(["git", "config", "user.name"], check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email"], check=True, capture_output=True)
            print("   ✅ Git config is set")
        except subprocess.CalledProcessError:
            print("   ⚠️  Git config not set (will be configured automatically)")
        
        # GitHub CLI check for PR creation
        if not self.dry_run:
            try:
                subprocess.run(["gh", "auth", "status"], check=True, capture_output=True)
                print("   ✅ GitHub CLI is authenticated")
            except (subprocess.CalledProcessError, FileNotFoundError):
                gh_token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
                if gh_token:
                    print("   ✅ GitHub token is available")
                else:
                    print("   ⚠️  GitHub CLI not authenticated and no token found")
        
        print()
        return True

    def load_classification(self) -> Optional[Dict]:
        """分類結果を読み込み"""
        try:
            if self.classification_file.exists():
                with open(self.classification_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️  Failed to load classification: {e}")
        return None

    def print_classification_summary(self, classification: Dict) -> None:
        """分類結果の要約を表示"""
        summary = classification.get("summary", {})
        total_files = classification.get("total_files", 0)
        translatable_files = classification.get("translatable_files", 0)
        
        print("📋 Classification Summary:")
        print(f"   Total files: {total_files}")
        print(f"   Translatable files: {translatable_files}")
        
        for category, files in summary.items():
            if files:
                category_names = {
                    "a": "🆕 New documents",
                    "b-1": "✏️  Updated (no conflicts)",
                    "b-2": "⚠️  Updated (with conflicts)",
                    "c": "📄 Non-translatable"
                }
                name = category_names.get(category, category)
                print(f"   {name}: {len(files)} files")
                
                # 最初の3ファイルのみ表示
                for file in files[:3]:
                    print(f"      - {file}")
                if len(files) > 3:
                    print(f"      ... and {len(files) - 3} more")
        print()

    def print_summary(self, success: bool = True) -> None:
        """実行結果の要約を表示"""
        duration = datetime.now() - self.start_time
        status = "✅ COMPLETED" if success else "❌ FAILED"
        
        print("=" * 60)
        print(f"🎯 Translation Pipeline {status}")
        print(f"   Target commit: {self.commit_hash}")
        print(f"   Mode: {self.mode}")
        print(f"   Duration: {duration.total_seconds():.1f}s")
        print(f"   Dry run: {self.dry_run}")
        
        # 開発モードの設定を表示
        if self.mode == "dev":
            if self.before_commit:
                print(f"   Before commit: {self.before_commit}")
            if self.limit:
                print(f"   File limit: {self.limit}")
            if self.paths:
                print(f"   Target paths: {', '.join(self.paths)}")
        
        # 分類結果があれば表示
        classification = self.load_classification()
        if classification:
            translatable_files = classification.get("translatable_files", 0)
            print(f"   Translatable files: {translatable_files}")
        
        print("=" * 60)

    def apply_dev_mode_filters(self, classification: Dict) -> Dict:
        """開発モード用のフィルタを適用"""
        if self.mode != "dev":
            return classification
            
        print("🔧 Applying dev mode filters...")
        
        # フィルタ前の状態を記録
        original_counts = {}
        for category in ["a", "b-1", "b-2", "c"]:
            original_counts[category] = len(classification.get("summary", {}).get(category, []))
        
        # before_commitフィルタ: 指定コミット以前の変更のみ対象
        if self.before_commit:
            print(f"   📅 Filtering files modified before commit: {self.before_commit}")
            classification = self._filter_by_before_commit(classification)
        
        # pathsフィルタ: 特定パスのファイルのみ対象
        if self.paths:
            print(f"   📁 Filtering by paths: {', '.join(self.paths)}")
            classification = self._filter_by_paths(classification)
        
        # limitフィルタ: 処理ファイル数制限
        if self.limit:
            print(f"   🔢 Limiting to {self.limit} files")
            classification = self._filter_by_limit(classification)
            
        # フィルタ後の状態を表示
        filtered_counts = {}
        for category in ["a", "b-1", "b-2", "c"]:
            filtered_counts[category] = len(classification.get("summary", {}).get(category, []))
            
        print("   📊 Filter results:")
        for category in ["a", "b-1", "b-2", "c"]:
            orig = original_counts[category]
            filt = filtered_counts[category]
            if orig != filt:
                print(f"      Category {category}: {orig} → {filt} files")
        
        # 翻訳対象ファイル数を再計算
        translatable_files = sum(len(files) for cat, files in classification.get("summary", {}).items() 
                                if cat in ["a", "b-1", "b-2"])
        classification["translatable_files"] = translatable_files
        
        print()
        return classification

    def check_sync_branch_exists(self) -> bool:
        """指定コミット以前の変更のみをフィルタ"""
        try:
            # before_commitより新しいコミットでの変更ファイルを除外
            result = subprocess.run(
                ["git", "diff", "--name-only", f"{self.before_commit}..HEAD"],
                capture_output=True, text=True, check=True,
                cwd=self.script_dir.parent.parent.parent
            )
            newer_files = set(result.stdout.strip().split('\n')) if result.stdout.strip() else set()
            
            # 各カテゴリから新しいファイルを除外
            summary = classification.get("summary", {})
            for category in ["a", "b-1", "b-2", "c"]:
                if category in summary:
                    summary[category] = [f for f in summary[category] if f not in newer_files]
                    
        except subprocess.CalledProcessError as e:
            print(f"      ⚠️  Warning: Could not filter by before_commit: {e}")
        
        return classification
        
    def _filter_by_paths(self, classification: Dict) -> Dict:
        """指定パスのファイルのみをフィルタ"""
        summary = classification.get("summary", {})
        for category in ["a", "b-1", "b-2", "c"]:
            if category in summary:
                summary[category] = [
                    f for f in summary[category] 
                    if any(f.startswith(path) for path in self.paths)
                ]
        return classification
        
    def _filter_by_limit(self, classification: Dict) -> Dict:
        """処理ファイル数を制限"""
        summary = classification.get("summary", {})
        
        # 翻訳対象ファイルを優先順位で収集（a > b-1 > b-2）
        all_translatable = []
        for category in ["a", "b-1", "b-2"]:
            if category in summary:
                for file in summary[category]:
                    all_translatable.append((category, file))
        
        # 制限数まで切り取り
        if len(all_translatable) > self.limit:
            limited_files = all_translatable[:self.limit]
            
            # 各カテゴリを更新
            new_summary = {"a": [], "b-1": [], "b-2": [], "c": summary.get("c", [])}
            for category, file in limited_files:
                new_summary[category].append(file)
            summary.update(new_summary)
            
        return classification
        """syncブランチが既に存在するかチェック"""
        # 完全ハッシュと短縮ハッシュの両方をチェック
        sync_branches = [
            f"sync-{self.commit_hash}",  # 完全版
            f"sync-{self.commit_hash[:7]}"  # 短縮版
        ]
        
        try:
            result = subprocess.run(
                ["git", "branch", "--list"],
                capture_output=True, text=True, check=True
            )
            existing_branches = [line.strip().lstrip('* ') for line in result.stdout.split('\n') if line.strip()]
            
            for sync_branch in sync_branches:
                if sync_branch in existing_branches:
                    print(f"   Found existing sync branch: {sync_branch}")
                    return True
            return False
        except:
            return False

    def cleanup_previous_state(self) -> None:
        """前回実行の残存状態をクリーンアップ"""
        print("🧹 Cleaning up previous state...")
        
        # 古いclassification.jsonを削除
        if self.classification_file.exists():
            try:
                self.classification_file.unlink()
                print(f"   ✅ Removed old classification file: {self.classification_file}")
            except Exception as e:
                print(f"   ⚠️  Failed to remove classification file: {e}")
        
        print()

    def run(self) -> bool:
        """パイプライン全体を実行"""
        try:
            # syncブランチが既に存在する場合は終了
            if self.check_sync_branch_exists():
                print(f"⏭️  Sync branch for commit {self.commit_hash} already exists, skipping pipeline execution")
                print(f"   If you want to re-run, delete the existing sync branch first:")
                print(f"   git branch -D sync-{self.commit_hash[:7]}  # or sync-{self.commit_hash}")
                print()
                self.print_summary(success=True)
                return True
            
            # 前回実行の残存状態をクリーンアップ
            self.cleanup_previous_state()
            
            # 前提条件チェック
            if not self.check_prerequisites():
                return False
            
            # Step 1: Fetch upstream changes
            success = self.run_step(
                "Fetch upstream", 
                ["python", "scripts/fetch_upstream.py", "--hash", self.commit_hash]
            )
            if not success:
                return False
            
            # Step 2: Classify changes
            success = self.run_step(
                "Classify changes",
                ["python", "scripts/classify_changes.py"]
            )
            if not success:
                return False
            
            # 分類結果をファイルに保存
            self.run_step(
                "Save classification",
                ["sh", "-c", "python scripts/classify_changes.py > classification.json"],
                required=True
            )
            
            # 分類結果を読み込み、翻訳が必要かチェック
            classification = self.load_classification()
            if not classification:
                print("⚠️  Could not load classification results")
                return False
            
            # 開発モードのフィルタを適用
            classification = self.apply_dev_mode_filters(classification)
            
            # フィルタ適用後の分類結果を保存
            if self.mode == "dev":
                try:
                    with open(self.classification_file, 'w', encoding='utf-8') as f:
                        json.dump(classification, f, ensure_ascii=False, indent=2)
                    print(f"   💾 Updated classification saved to {self.classification_file}")
                except Exception as e:
                    print(f"   ⚠️  Failed to save filtered classification: {e}")
            
            self.print_classification_summary(classification)
            
            translatable_files = classification.get("translatable_files", 0)
            if translatable_files == 0:
                print("📋 No files to translate, skipping translation steps...")
                
                # 翻訳不要でもコミット＆PR作成は実行（マージコミットなど）
                success = self.run_step(
                    "Create commit and PR",
                    ["python", "scripts/commit_and_pr.py", 
                     "--classification", str(self.classification_file)],
                    required=False
                )
                
                self.print_summary(success=True)
                return True
            
            print(f"📝 Found {translatable_files} files to translate, proceeding...")
            
            # Step 3: Translate files
            success = self.run_step(
                "Translate files",
                ["python", "scripts/translate_chunk.py", 
                 "--classification", str(self.classification_file),
                 "--mode", "all"],
                env_vars={"GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", "")}
            )
            if not success:
                return False
            
            # Step 4: Post-process translations
            success = self.run_step(
                "Post-process translations",
                ["python", "scripts/postprocess.py",
                 "--classification", str(self.classification_file)]
            )
            if not success:
                return False
            
            # Step 5: Commit and create PR
            success = self.run_step(
                "Create commit and PR",
                ["python", "scripts/commit_and_pr.py",
                 "--classification", str(self.classification_file)],
                env_vars={
                    "GH_TOKEN": os.getenv("GH_TOKEN", ""),
                    "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN", "")
                }
            )
            if not success:
                return False
            
            self.print_summary(success=True)
            return True
            
        except KeyboardInterrupt:
            print("\n\n💥 Pipeline interrupted by user")
            self.print_summary(success=False)
            return False
        except Exception as e:
            print(f"\n\n💥 Unexpected error: {e}")
            self.print_summary(success=False)
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Run complete translation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with specific commit hash
  python run_translation_pipeline.py --hash 90d107e2
  
  # Dry run (no actual translation/commit/PR)
  python run_translation_pipeline.py --hash 90d107e2 --dry-run
  
  # Run with latest upstream commit
  python run_translation_pipeline.py --hash HEAD
  
  # Development mode with filters
  python run_translation_pipeline.py --mode dev --hash HEAD --limit 5
  python run_translation_pipeline.py --mode dev --before abc1234 --paths docs/
        """
    )
    
    parser.add_argument(
        "--hash",
        default="HEAD",
        help="Target upstream commit hash (default: HEAD)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (skip translation, commit, and PR creation)"
    )
    
    parser.add_argument(
        "--mode",
        choices=["normal", "dev"],
        default="normal",
        help="Pipeline mode: normal (default) or dev (development with filters)"
    )
    
    # 開発モード専用オプション
    dev_group = parser.add_argument_group("development mode options")
    dev_group.add_argument(
        "--before",
        dest="before_commit",
        help="Process only files modified before this commit (dev mode only)"
    )
    
    dev_group.add_argument(
        "--limit",
        type=int,
        help="Limit number of files to process (dev mode only)"
    )
    
    dev_group.add_argument(
        "--paths",
        nargs="+",
        help="Process only files under these paths (dev mode only)"
    )
    
    args = parser.parse_args()
    
    # 開発モード専用オプションの検証
    if args.mode != "dev":
        dev_options = [args.before_commit, args.limit, args.paths]
        if any(opt is not None for opt in dev_options):
            print("❌ Development mode options (--before, --limit, --paths) can only be used with --mode dev")
            sys.exit(1)
    
    # 作業ディレクトリを確認
    if not Path(".github/auto-translation").exists():
        print("❌ This script must be run from the repository root")
        print("   Current directory should contain .github/auto-translation/")
        sys.exit(1)
    
    # パイプライン実行
    pipeline = TranslationPipeline(
        args.hash, 
        args.dry_run, 
        args.mode,
        args.before_commit,
        args.limit,
        args.paths
    )
    success = pipeline.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()