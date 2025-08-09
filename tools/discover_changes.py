#!/usr/bin/env python3
"""
差分検出器：upstream英語原文と既存日本語訳との差分検出を自動化

機能:
- difflib.SequenceMatcherを使用したdiff検出
- 軽微変更の判定とスキップ (空白・句読点のみ、トークン数ベース)
- Gemini AIによる意味変化判定 (YES/NO)
- 全オペコード対応 (equal/insert/delete/replace)
"""

import difflib
import re
import json
import argparse
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ChangeOperation:
    """差分操作を表すデータクラス"""
    opcode: str  # equal, insert, delete, replace
    source_start: int
    source_end: int
    target_start: int
    target_end: int
    source_text: str
    target_text: str
    is_minor_change: bool = False
    has_semantic_change: Optional[bool] = None


class MinorChangeDetector:
    """軽微変更の検出器"""
    
    @staticmethod
    def is_whitespace_punctuation_only(text1: str, text2: str) -> bool:
        """空白・句読点のみの変更かどうかを判定"""
        # 英数字・ひらがな・カタカナ・漢字以外の文字を除去して比較
        pattern = r'[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]'
        clean1 = re.sub(pattern, '', text1, flags=re.UNICODE)
        clean2 = re.sub(pattern, '', text2, flags=re.UNICODE)
        return clean1 == clean2
    
    @staticmethod
    def is_token_count_similar(text1: str, text2: str, threshold: float = 0.1) -> bool:
        """トークン数が類似しているかどうかを判定"""
        tokens1 = re.findall(r'\w+', text1, re.UNICODE)
        tokens2 = re.findall(r'\w+', text2, re.UNICODE)
        
        if len(tokens1) == 0 and len(tokens2) == 0:
            return True
        
        max_len = max(len(tokens1), len(tokens2))
        if max_len == 0:
            return True
            
        diff_ratio = abs(len(tokens1) - len(tokens2)) / max_len
        return diff_ratio <= threshold
    
    @classmethod
    def is_minor_change(cls, text1: str, text2: str) -> bool:
        """軽微変更かどうかを総合判定"""
        return (cls.is_whitespace_punctuation_only(text1, text2) or
                cls.is_token_count_similar(text1, text2))


class SemanticChangeDetector:
    """意味変化検出器 (Gemini AI使用)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        # TODO: Gemini API実装は後で追加
        logger.warning("Gemini API integration not yet implemented")
    
    def has_semantic_change(self, original: str, modified: str) -> Optional[bool]:
        """意味変化があるかどうかを判定 (現在はプレースホルダー)"""
        # プレースホルダー実装: 後でGemini APIを使用
        if not self.api_key:
            logger.warning("No API key provided for semantic analysis")
            return None
        
        # TODO: Gemini APIを呼び出して意味変化を判定
        # 現在は単純なヒューリスティック
        if len(original.strip()) == 0 or len(modified.strip()) == 0:
            return True
        
        # 文字数の大幅な変化は意味変化の可能性が高い
        len_ratio = min(len(original), len(modified)) / max(len(original), len(modified))
        return len_ratio < 0.5


class DiffDiscoverer:
    """差分検出メインクラス"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.minor_detector = MinorChangeDetector()
        self.semantic_detector = SemanticChangeDetector(api_key)
    
    def discover_changes(self, source_lines: List[str], target_lines: List[str]) -> List[ChangeOperation]:
        """差分を検出してChangeOperationのリストを返す"""
        matcher = difflib.SequenceMatcher(None, source_lines, target_lines)
        operations = []
        
        for opcode, source_start, source_end, target_start, target_end in matcher.get_opcodes():
            source_text = '\n'.join(source_lines[source_start:source_end])
            target_text = '\n'.join(target_lines[target_start:target_end])
            
            operation = ChangeOperation(
                opcode=opcode,
                source_start=source_start,
                source_end=source_end,
                target_start=target_start,
                target_end=target_end,
                source_text=source_text,
                target_text=target_text
            )
            
            # 軽微変更の判定
            if opcode == 'replace':
                operation.is_minor_change = self.minor_detector.is_minor_change(
                    source_text, target_text
                )
            
            # 意味変化の判定 (equal以外)
            if opcode != 'equal':
                operation.has_semantic_change = self.semantic_detector.has_semantic_change(
                    source_text, target_text
                )
            
            operations.append(operation)
        
        return operations
    
    def discover_from_files(self, source_file: str, target_file: str) -> List[ChangeOperation]:
        """ファイルから差分を検出"""
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                source_lines = f.readlines()
            
            with open(target_file, 'r', encoding='utf-8') as f:
                target_lines = f.readlines()
            
            # 改行文字を除去
            source_lines = [line.rstrip('\n\r') for line in source_lines]
            target_lines = [line.rstrip('\n\r') for line in target_lines]
            
            return self.discover_changes(source_lines, target_lines)
        
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading files: {e}")
            raise


def serialize_operations(operations: List[ChangeOperation]) -> str:
    """ChangeOperationのリストをJSON文字列にシリアライズ"""
    data = []
    for op in operations:
        data.append({
            'opcode': op.opcode,
            'source_start': op.source_start,
            'source_end': op.source_end,
            'target_start': op.target_start,
            'target_end': op.target_end,
            'source_text': op.source_text,
            'target_text': op.target_text,
            'is_minor_change': op.is_minor_change,
            'has_semantic_change': op.has_semantic_change
        })
    return json.dumps(data, ensure_ascii=False, indent=2)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='Discover changes between source and target files')
    parser.add_argument('source_file', help='Source file path')
    parser.add_argument('target_file', help='Target file path')
    parser.add_argument('--output', '-o', help='Output JSON file')
    parser.add_argument('--api-key', help='Gemini API key for semantic analysis')
    parser.add_argument('--skip-minor', action='store_true', help='Skip minor changes in output')
    
    args = parser.parse_args()
    
    try:
        discoverer = DiffDiscoverer(api_key=args.api_key)
        operations = discoverer.discover_from_files(args.source_file, args.target_file)
        
        # 軽微変更をスキップする場合
        if args.skip_minor:
            operations = [op for op in operations if not op.is_minor_change]
        
        # 結果を出力
        result_json = serialize_operations(operations)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result_json)
            logger.info(f"Results written to {args.output}")
        else:
            print(result_json)
        
        # サマリーを出力
        total_ops = len(operations)
        by_opcode = {}
        minor_count = 0
        semantic_count = 0
        
        for op in operations:
            by_opcode[op.opcode] = by_opcode.get(op.opcode, 0) + 1
            if op.is_minor_change:
                minor_count += 1
            if op.has_semantic_change:
                semantic_count += 1
        
        logger.info(f"Total operations: {total_ops}")
        logger.info(f"By opcode: {by_opcode}")
        logger.info(f"Minor changes: {minor_count}")
        logger.info(f"Semantic changes: {semantic_count}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())