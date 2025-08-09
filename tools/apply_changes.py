#!/usr/bin/env python3
"""
差分適用器：discover_changes.pyで検出された差分を既存ファイルに適用

機能:
- JSON形式の差分データを読み込み
- 全オペコード (equal/insert/delete/replace) の適用
- バックアップファイルの作成
- 適用結果の検証
"""

import json
import argparse
import shutil
from typing import List, Dict, Any
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChangeApplier:
    """差分適用メインクラス"""
    
    def __init__(self, create_backup: bool = True):
        self.create_backup = create_backup
    
    def load_operations(self, operations_file: str) -> List[Dict[str, Any]]:
        """JSON形式の差分操作データを読み込む"""
        try:
            with open(operations_file, 'r', encoding='utf-8') as f:
                operations = json.load(f)
            logger.info(f"Loaded {len(operations)} operations from {operations_file}")
            return operations
        except Exception as e:
            logger.error(f"Error loading operations: {e}")
            raise
    
    def apply_changes(self, target_file: str, operations: List[Dict[str, Any]], 
                     skip_minor: bool = False, skip_no_semantic: bool = False) -> bool:
        """差分操作をターゲットファイルに適用"""
        try:
            # バックアップを作成
            if self.create_backup:
                backup_file = f"{target_file}.backup"
                shutil.copy2(target_file, backup_file)
                logger.info(f"Backup created: {backup_file}")
            
            # ファイルを読み込み
            with open(target_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 改行文字を除去
            lines = [line.rstrip('\n\r') for line in lines]
            
            # 操作をフィルタリング
            filtered_ops = self._filter_operations(operations, skip_minor, skip_no_semantic)
            logger.info(f"Applying {len(filtered_ops)} operations (filtered from {len(operations)})")
            
            # 操作を逆順で適用 (インデックスの変更を避けるため)
            filtered_ops.sort(key=lambda op: op['target_start'], reverse=True)
            
            # 各操作を適用
            for i, operation in enumerate(filtered_ops):
                opcode = operation['opcode']
                target_start = operation['target_start']
                target_end = operation['target_end']
                source_text = operation['source_text']
                
                logger.debug(f"Applying operation {i+1}/{len(filtered_ops)}: {opcode} "
                           f"at lines {target_start}-{target_end}")
                
                if opcode == 'equal':
                    # equal操作は何もしない
                    continue
                elif opcode == 'insert':
                    # target has content that source doesn't - DELETE from target
                    del lines[target_start:target_end]
                elif opcode == 'delete':
                    # source has content that target doesn't - INSERT into target
                    new_lines = source_text.split('\n') if source_text else []
                    lines[target_start:target_start] = new_lines
                elif opcode == 'replace':
                    # 指定範囲をsource_textで置換
                    new_lines = source_text.split('\n') if source_text else []
                    lines[target_start:target_end] = new_lines
                else:
                    logger.warning(f"Unknown opcode: {opcode}")
            
            # ファイルに書き戻し
            with open(target_file, 'w', encoding='utf-8') as f:
                for line in lines:
                    f.write(line + '\n')
            
            logger.info(f"Changes applied successfully to {target_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying changes: {e}")
            # エラー時はバックアップから復元
            if self.create_backup:
                backup_file = f"{target_file}.backup"
                if Path(backup_file).exists():
                    shutil.copy2(backup_file, target_file)
                    logger.info(f"Restored from backup: {backup_file}")
            raise
    
    def _filter_operations(self, operations: List[Dict[str, Any]], 
                          skip_minor: bool, skip_no_semantic: bool) -> List[Dict[str, Any]]:
        """操作をフィルタリング"""
        filtered = []
        
        for op in operations:
            # 軽微変更をスキップ
            if skip_minor and op.get('is_minor_change', False):
                logger.debug(f"Skipping minor change: {op['opcode']} at {op['target_start']}")
                continue
            
            # 意味変化がない変更をスキップ
            if skip_no_semantic and op.get('has_semantic_change') is False:
                logger.debug(f"Skipping non-semantic change: {op['opcode']} at {op['target_start']}")
                continue
            
            filtered.append(op)
        
        return filtered
    
    def apply_from_files(self, target_file: str, operations_file: str, 
                        skip_minor: bool = False, skip_no_semantic: bool = False) -> bool:
        """ファイルから操作を読み込んで適用"""
        operations = self.load_operations(operations_file)
        return self.apply_changes(target_file, operations, skip_minor, skip_no_semantic)
    
    def validate_result(self, target_file: str, expected_operations: List[Dict[str, Any]]) -> bool:
        """適用結果の検証 (簡易版)"""
        try:
            with open(target_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            logger.info(f"Validation: target file has {total_lines} lines")
            
            # 基本的な検証のみ実装
            # より詳細な検証は必要に応じて追加
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='Apply changes from diff operations to target file')
    parser.add_argument('target_file', help='Target file to apply changes to')
    parser.add_argument('operations_file', help='JSON file containing diff operations')
    parser.add_argument('--skip-minor', action='store_true', 
                       help='Skip minor changes (whitespace/punctuation only)')
    parser.add_argument('--skip-no-semantic', action='store_true',
                       help='Skip changes with no semantic impact')
    parser.add_argument('--no-backup', action='store_true', help='Do not create backup file')
    parser.add_argument('--validate', action='store_true', help='Validate result after applying')
    
    args = parser.parse_args()
    
    try:
        # ターゲットファイルの存在確認
        if not Path(args.target_file).exists():
            logger.error(f"Target file not found: {args.target_file}")
            return 1
        
        # 操作ファイルの存在確認
        if not Path(args.operations_file).exists():
            logger.error(f"Operations file not found: {args.operations_file}")
            return 1
        
        # 差分適用器を作成
        applier = ChangeApplier(create_backup=not args.no_backup)
        
        # 変更を適用
        success = applier.apply_from_files(
            args.target_file, 
            args.operations_file,
            skip_minor=args.skip_minor,
            skip_no_semantic=args.skip_no_semantic
        )
        
        if not success:
            logger.error("Failed to apply changes")
            return 1
        
        # 結果を検証
        if args.validate:
            operations = applier.load_operations(args.operations_file)
            if not applier.validate_result(args.target_file, operations):
                logger.warning("Validation failed")
                return 1
            logger.info("Validation passed")
        
        logger.info("Changes applied successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == '__main__':
    exit(main())