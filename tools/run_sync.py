#!/usr/bin/env python3
"""
Synchronization and translation tool for JHipster Japanese documentation.

This tool handles:
- Syncing content from upstream repository
- Translation workflow with LLM integration
- Safety guards for fork vs main repository operations
- PR generation and management
"""

import os
import sys
import argparse
import json
import subprocess
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class SyncGuard:
    """Safety guard system for sync operations."""
    
    def __init__(self, github_repository: str, github_event_name: str):
        self.github_repository = github_repository
        self.github_event_name = github_event_name
        self.is_fork = self._detect_fork()
        self.is_main_repo = self._detect_main_repo()
        
    def _detect_fork(self) -> bool:
        """Detect if running in a fork repository."""
        # The main repository is jhipster/jhipster.github.io
        # This fork is hide212131/jp
        return 'hide212131/jp' in self.github_repository
        
    def _detect_main_repo(self) -> bool:
        """Detect if running in the main upstream repository."""
        return 'jhipster/jhipster.github.io' in self.github_repository
        
    def should_run_sync(self) -> Tuple[bool, str]:
        """Determine if sync operation should proceed based on context."""
        if self.is_main_repo:
            return False, "Sync operations should not run on main upstream repository"
            
        if self.is_fork and self.github_event_name == 'schedule':
            return True, "Scheduled sync allowed on fork"
            
        if self.is_fork and self.github_event_name == 'workflow_dispatch':
            return True, "Manual sync allowed on fork"
            
        if self.github_event_name == 'pull_request':
            return False, "Sync operations disabled on PR events"
            
        return False, f"Sync not allowed for event: {self.github_event_name} on repo: {self.github_repository}"
        
    def should_create_pr(self) -> Tuple[bool, str]:
        """Determine if PR creation is allowed."""
        if not self.is_fork:
            return False, "PR creation only allowed from forks"
            
        return True, "PR creation allowed"


class SyncRunner:
    """Main sync operation runner."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.github_repository = os.getenv('GITHUB_REPOSITORY', 'unknown/unknown')
        self.github_event_name = os.getenv('GITHUB_EVENT_NAME', 'unknown')
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        self.guard = SyncGuard(self.github_repository, self.github_event_name)
        
    def check_environment(self) -> List[str]:
        """Check required environment and return any issues."""
        issues = []
        
        if not self.github_token:
            issues.append("GITHUB_TOKEN not found in environment")
            
        if not self.gemini_api_key:
            issues.append("GEMINI_API_KEY not found in environment (required for translation)")
            
        return issues
        
    def log_status(self, message: str, level: str = "INFO"):
        """Log status message with timestamp."""
        print(f"[{level}] {message}")
        
    def run_sync(self) -> int:
        """Execute the sync operation."""
        self.log_status("=== JHipster JP Sync Tool ===")
        self.log_status(f"Repository: {self.github_repository}")
        self.log_status(f"Event: {self.github_event_name}")
        self.log_status(f"Dry run: {self.dry_run}")
        self.log_status(f"Is fork: {self.guard.is_fork}")
        self.log_status(f"Is main repo: {self.guard.is_main_repo}")
        
        # Check environment
        env_issues = self.check_environment()
        if env_issues:
            for issue in env_issues:
                self.log_status(issue, "WARNING")
                
        # Check sync permission
        should_sync, sync_reason = self.guard.should_run_sync()
        self.log_status(f"Sync permission: {should_sync} - {sync_reason}")
        
        if not should_sync:
            self.log_status("Sync operation blocked by safety guard", "ERROR")
            return 1
            
        # Check PR creation permission
        should_create_pr, pr_reason = self.guard.should_create_pr()
        self.log_status(f"PR creation permission: {should_create_pr} - {pr_reason}")
        
        if self.dry_run:
            return self._run_dry_run()
        else:
            return self._run_actual_sync()
            
    def _run_dry_run(self) -> int:
        """Run in dry-run mode to generate PR template."""
        self.log_status("=== DRY RUN MODE ===")
        
        # Generate PR template
        pr_template = self._generate_pr_template()
        
        # Write template to file
        template_path = Path("sync_pr_template.md")
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(pr_template)
            
        self.log_status(f"PR template generated: {template_path}")
        
        return 0
        
    def _run_actual_sync(self) -> int:
        """Run actual sync operation."""
        self.log_status("=== ACTUAL SYNC MODE ===")
        
        # This would contain the actual sync logic
        # For now, just log what would happen
        self.log_status("Would perform upstream sync...")
        self.log_status("Would run translation pipeline...")
        self.log_status("Would create PR if changes detected...")
        
        return 0
        
    def _generate_pr_template(self) -> str:
        """Generate PR template content."""
        return f"""# 自動同期・翻訳PR

## 概要
上流リポジトリからの自動同期と翻訳処理の結果です。

## 実行情報
- Repository: {self.github_repository}
- Event: {self.github_event_name}
- Timestamp: {self._get_timestamp()}

## 変更内容
- [ ] 上流からの新規コンテンツ同期
- [ ] 既存コンテンツの更新同期
- [ ] 翻訳処理の実行
- [ ] リンク・参照の調整

## 確認事項
- [ ] 翻訳品質の確認
- [ ] リンク切れのチェック
- [ ] フォーマットの確認
- [ ] 用語統一の確認

## 注意事項
このPRは自動生成されました。レビュー後にマージしてください。

---
Generated by JHipster JP Sync Tool (dry-run mode)
"""

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="JHipster JP Sync Tool")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Run in dry-run mode (generate PR template only)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    runner = SyncRunner(dry_run=args.dry_run)
    return runner.run_sync()


if __name__ == "__main__":
    sys.exit(main())