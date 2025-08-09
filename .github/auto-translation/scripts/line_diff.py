#!/usr/bin/env python3
"""
JHipster日本語ドキュメント自動翻訳システム
行レベル差分検出・操作モジュール
"""

import difflib
import re
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum


class OperationType(Enum):
    """差分操作タイプ"""
    EQUAL = "equal"
    INSERT = "insert"
    DELETE = "delete"
    REPLACE = "replace"


@dataclass
class LineOperation:
    """行操作を表すデータクラス"""
    operation: OperationType
    old_start: int
    old_end: int
    new_start: int
    new_end: int
    old_lines: List[str]
    new_lines: List[str]
    similarity_ratio: float = 0.0
    
    def __post_init__(self):
        """操作後の初期化処理"""
        if self.operation == OperationType.REPLACE and self.old_lines and self.new_lines:
            # 置換操作の場合、類似度を計算
            self.similarity_ratio = self._calculate_similarity()
    
    def _calculate_similarity(self) -> float:
        """行間の類似度を計算"""
        if not self.old_lines or not self.new_lines:
            return 0.0
        
        old_text = "\n".join(self.old_lines)
        new_text = "\n".join(self.new_lines)
        
        return difflib.SequenceMatcher(None, old_text, new_text).ratio()
    
    def is_minor_change(self, threshold: float = 0.90) -> bool:
        """軽微変更かどうか判定"""
        if self.operation != OperationType.REPLACE:
            return False
        
        if self.similarity_ratio < threshold:
            return False
        
        # トークン数の類似性をチェック
        old_tokens = self._tokenize_content("\n".join(self.old_lines))
        new_tokens = self._tokenize_content("\n".join(self.new_lines))
        
        # トークン数の差が20%以内に緩和
        if len(old_tokens) > 0:
            token_ratio = abs(len(new_tokens) - len(old_tokens)) / len(old_tokens)
            if token_ratio > 0.2:
                return False
        
        # 主要な変更が句読点・空白のみかチェック
        return self._is_punctuation_whitespace_only_change()
    
    def _tokenize_content(self, content: str) -> List[str]:
        """コンテンツをトークンに分割"""
        # 単語境界で分割（英語・日本語対応）
        pattern = r'\b\w+\b|[^\w\s]'
        return re.findall(pattern, content, re.UNICODE)
    
    def _is_punctuation_whitespace_only_change(self) -> bool:
        """句読点・空白のみの変更かチェック"""
        if not self.old_lines or not self.new_lines:
            return False
        
        old_content = "".join(self.old_lines)
        new_content = "".join(self.new_lines)
        
        # 英数字・日本語文字を除去して比較
        old_cleaned = re.sub(r'[a-zA-Z0-9\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', '', old_content)
        new_cleaned = re.sub(r'[a-zA-Z0-9\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', '', new_content)
        
        # 実質的な文字が同じで、句読点・空白のみ異なる
        old_essential = re.sub(r'[^\w]', '', old_content, flags=re.UNICODE)
        new_essential = re.sub(r'[^\w]', '', new_content, flags=re.UNICODE)
        
        return old_essential == new_essential


class LineDiffAnalyzer:
    """行レベル差分分析器"""
    
    def __init__(self):
        self.operations: List[LineOperation] = []
    
    def analyze_diff(self, old_lines: List[str], new_lines: List[str]) -> List[LineOperation]:
        """2つのファイルの行レベル差分を分析"""
        self.operations = []
        
        # difflib.SequenceMatcherを使用して差分を取得
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            old_chunk = old_lines[i1:i2]
            new_chunk = new_lines[j1:j2]
            
            if tag == 'equal':
                operation = LineOperation(
                    operation=OperationType.EQUAL,
                    old_start=i1, old_end=i2,
                    new_start=j1, new_end=j2,
                    old_lines=old_chunk,
                    new_lines=new_chunk
                )
            elif tag == 'insert':
                operation = LineOperation(
                    operation=OperationType.INSERT,
                    old_start=i1, old_end=i2,
                    new_start=j1, new_end=j2,
                    old_lines=[],
                    new_lines=new_chunk
                )
            elif tag == 'delete':
                operation = LineOperation(
                    operation=OperationType.DELETE,
                    old_start=i1, old_end=i2,
                    new_start=j1, new_end=j2,
                    old_lines=old_chunk,
                    new_lines=[]
                )
            elif tag == 'replace':
                operation = LineOperation(
                    operation=OperationType.REPLACE,
                    old_start=i1, old_end=i2,
                    new_start=j1, new_end=j2,
                    old_lines=old_chunk,
                    new_lines=new_chunk
                )
            else:
                continue
            
            self.operations.append(operation)
        
        return self.operations
    
    def get_change_summary(self) -> Dict[str, Any]:
        """変更の要約を取得"""
        summary = {
            "total_operations": len(self.operations),
            "equal_count": 0,
            "insert_count": 0,
            "delete_count": 0,
            "replace_count": 0,
            "minor_changes": 0,
            "major_changes": 0
        }
        
        for op in self.operations:
            if op.operation == OperationType.EQUAL:
                summary["equal_count"] += 1
            elif op.operation == OperationType.INSERT:
                summary["insert_count"] += 1
            elif op.operation == OperationType.DELETE:
                summary["delete_count"] += 1
            elif op.operation == OperationType.REPLACE:
                summary["replace_count"] += 1
                if op.is_minor_change():
                    summary["minor_changes"] += 1
                else:
                    summary["major_changes"] += 1
        
        return summary
    
    def find_operations_by_type(self, operation_type: OperationType) -> List[LineOperation]:
        """指定された操作タイプの操作リストを取得"""
        return [op for op in self.operations if op.operation == operation_type]
    
    def has_significant_changes(self) -> bool:
        """重要な変更があるかチェック"""
        for op in self.operations:
            if op.operation in [OperationType.INSERT, OperationType.DELETE]:
                return True
            elif op.operation == OperationType.REPLACE and not op.is_minor_change():
                return True
        return False


def analyze_file_diff(old_content: str, new_content: str) -> LineDiffAnalyzer:
    """ファイル内容の差分を分析"""
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()
    
    analyzer = LineDiffAnalyzer()
    analyzer.analyze_diff(old_lines, new_lines)
    
    return analyzer


def format_operation_report(operations: List[LineOperation]) -> str:
    """操作リストのレポートを整形"""
    report_lines = []
    
    for i, op in enumerate(operations):
        report_lines.append(f"操作 {i + 1}: {op.operation.value}")
        report_lines.append(f"  旧: 行 {op.old_start}-{op.old_end} ({len(op.old_lines)} lines)")
        report_lines.append(f"  新: 行 {op.new_start}-{op.new_end} ({len(op.new_lines)} lines)")
        
        if op.operation == OperationType.REPLACE:
            report_lines.append(f"  類似度: {op.similarity_ratio:.3f}")
            report_lines.append(f"  軽微変更: {'Yes' if op.is_minor_change() else 'No'}")
        
        if op.old_lines:
            report_lines.append("  削除行:")
            for line in op.old_lines[:3]:  # 最初の3行のみ表示
                report_lines.append(f"    - {line}")
            if len(op.old_lines) > 3:
                report_lines.append(f"    ... および {len(op.old_lines) - 3} 行")
        
        if op.new_lines:
            report_lines.append("  追加行:")
            for line in op.new_lines[:3]:  # 最初の3行のみ表示
                report_lines.append(f"    + {line}")
            if len(op.new_lines) > 3:
                report_lines.append(f"    ... および {len(op.new_lines) - 3} 行")
        
        report_lines.append("")
    
    return "\n".join(report_lines)