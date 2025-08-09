#!/usr/bin/env python3
"""
JHipster日本語ドキュメント自動翻訳システム
変更適用スクリプト：ポリシーに従い既訳温存/新規翻訳/削除/再翻訳を適用
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import google.generativeai as genai

# プロジェクトルートに line_diff モジュールを追加
sys.path.insert(0, os.path.dirname(__file__))
from line_diff import OperationType, LineOperation, LineDiffAnalyzer


def find_project_root() -> Path:
    """プロジェクトルートディレクトリを見つける"""
    current = Path(__file__).parent.parent.parent.parent
    while current != current.parent:
        if (current / '.git').exists() or (current / 'package.json').exists():
            return current
        current = current.parent
    return Path.cwd()


class ChangePolicy(Enum):
    """変更適用ポリシー"""
    KEEP_EXISTING = "keep_existing"      # 既訳維持
    NEW_TRANSLATION = "new_translation"  # 新規翻訳
    DELETE = "delete"                    # 削除
    RETRANSLATE = "retranslate"         # 再翻訳


@dataclass
class ApplicationResult:
    """適用結果"""
    file_path: str
    policy: ChangePolicy
    applied: bool
    reason: str
    original_lines: List[str]
    translated_lines: List[str]
    error: Optional[str] = None


class SemanticChangeDetector:
    """LLMベースの意味変更検出器"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
    
    def has_semantic_change(self, old_text: str, new_text: str) -> bool:
        """意味的な変更があるかLLMで判定（YES/NOのみ）"""
        if not self.model:
            # LLMが利用できない場合はデフォルト判定
            return self._fallback_semantic_detection(old_text, new_text)
        
        try:
            prompt = self._create_semantic_change_prompt(old_text, new_text)
            response = self.model.generate_content(prompt)
            
            # YES/NOの回答を解析
            answer = response.text.strip().upper()
            return answer.startswith('YES')
            
        except Exception as e:
            print(f"Warning: LLM semantic detection failed: {e}")
            return self._fallback_semantic_detection(old_text, new_text)
    
    def _create_semantic_change_prompt(self, old_text: str, new_text: str) -> str:
        """意味変更判定用のプロンプトを作成"""
        return f"""以下の2つのテキストを比較して、意味的な変更があるかどうかを判定してください。

回答は「YES」または「NO」のみで答えてください。理由は不要です。

判定基準：
- 単なる句読点や空白の変更 → NO
- 表記の軽微な変更（英数字の半角/全角など） → NO
- 内容の追加・削除・変更 → YES
- 文章構造の変更 → YES
- リンクやコードの変更 → YES

旧テキスト:
```
{old_text}
```

新テキスト:
```
{new_text}
```

回答:"""
    
    def _fallback_semantic_detection(self, old_text: str, new_text: str) -> bool:
        """LLMが利用できない場合のフォールバック判定"""
        # 簡単なヒューリスティック判定
        import re
        
        # 英数字・日本語文字のみを抽出して比較
        old_essential = re.sub(r'[^\w]', '', old_text, flags=re.UNICODE)
        new_essential = re.sub(r'[^\w]', '', new_text, flags=re.UNICODE)
        
        # 文字列長の変化が10%以上の場合は意味変更とみなす
        if len(old_essential) > 0:
            change_ratio = abs(len(new_essential) - len(old_essential)) / len(old_essential)
            return change_ratio > 0.1
        
        return old_essential != new_essential


class ChangeApplicator:
    """変更適用器"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or find_project_root()
        self.semantic_detector = SemanticChangeDetector()
        self.translation_cache = {}  # 翻訳キャッシュ
    
    def determine_policy(self, operation: Dict[str, Any], existing_translation: str = None) -> ChangePolicy:
        """操作に対する適用ポリシーを決定"""
        op_type = operation["operation"]
        
        if op_type == "equal":
            return ChangePolicy.KEEP_EXISTING
        
        elif op_type == "insert":
            return ChangePolicy.NEW_TRANSLATION
        
        elif op_type == "delete":
            return ChangePolicy.DELETE
        
        elif op_type == "replace":
            # 軽微変更の場合は既訳維持
            if operation.get("is_minor_change", False):
                return ChangePolicy.KEEP_EXISTING
            
            # LLMによる意味判定
            old_text = "\n".join(operation["old_lines"])
            new_text = "\n".join(operation["new_lines"])
            
            if self.semantic_detector.has_semantic_change(old_text, new_text):
                return ChangePolicy.RETRANSLATE
            else:
                return ChangePolicy.KEEP_EXISTING
        
        return ChangePolicy.KEEP_EXISTING
    
    def apply_operation(
        self,
        operation: Dict[str, Any],
        existing_translation: List[str],
        policy: ChangePolicy = None
    ) -> Tuple[List[str], str]:
        """単一操作を適用"""
        if policy is None:
            existing_text = "\n".join(existing_translation[operation["old_start"]:operation["old_end"]])
            policy = self.determine_policy(operation, existing_text)
        
        result_lines = existing_translation.copy()
        reason = ""
        
        old_start = operation["old_start"]
        old_end = operation["old_end"]
        new_lines = operation["new_lines"]
        
        if policy == ChangePolicy.KEEP_EXISTING:
            reason = "既訳を維持（軽微変更またはスタイル変更のみ）"
            # 何もしない
        
        elif policy == ChangePolicy.NEW_TRANSLATION:
            reason = "新規翻訳が必要"
            # 新規行を挿入位置に追加
            insert_pos = old_start
            
            # 翻訳が必要な場合は、元の英語テキストをそのまま挿入
            # 実際の翻訳は別の処理で行う
            translated_lines = self._translate_lines(new_lines)
            result_lines[insert_pos:insert_pos] = translated_lines
        
        elif policy == ChangePolicy.DELETE:
            reason = "削除された内容のため除去"
            # 該当範囲を削除
            del result_lines[old_start:old_end]
        
        elif policy == ChangePolicy.RETRANSLATE:
            reason = "意味的変更のため再翻訳"
            # 既存の翻訳を新しい翻訳で置換
            translated_lines = self._translate_lines(new_lines)
            result_lines[old_start:old_end] = translated_lines
        
        return result_lines, reason
    
    def _translate_lines(self, lines: List[str]) -> List[str]:
        """行を翻訳（実際の翻訳はモックまたは別システム）"""
        # この関数では実際の翻訳は行わず、翻訳が必要なマーカーを付ける
        # 実際の翻訳は translate_chunk.py などの既存システムを使用
        translated = []
        for line in lines:
            if line.strip():
                translated.append(f"[要翻訳] {line}")
            else:
                translated.append(line)
        return translated
    
    def apply_file_changes(
        self,
        file_path: str,
        operations: List[Dict[str, Any]],
        existing_translation: str = None
    ) -> ApplicationResult:
        """ファイル全体の変更を適用"""
        try:
            # 既存の翻訳を取得
            if existing_translation is None:
                full_path = self.project_root / file_path
                if full_path.exists():
                    with open(full_path, 'r', encoding='utf-8') as f:
                        existing_translation = f.read()
                else:
                    existing_translation = ""
            
            # 行に分割
            result_lines = existing_translation.splitlines()
            original_lines = result_lines.copy()
            
            # 操作を逆順で適用（インデックスの整合性を保つため）
            operations_sorted = sorted(operations, key=lambda op: op["old_start"], reverse=True)
            
            applied_policies = []
            all_reasons = []
            
            for operation in operations_sorted:
                policy = self.determine_policy(operation)
                result_lines, reason = self.apply_operation(operation, result_lines, policy)
                
                applied_policies.append(policy)
                all_reasons.append(f"{operation['operation']}: {reason}")
            
            # 結果を確定
            final_policy = self._determine_overall_policy(applied_policies)
            combined_reason = "; ".join(all_reasons)
            
            return ApplicationResult(
                file_path=file_path,
                policy=final_policy,
                applied=True,
                reason=combined_reason,
                original_lines=original_lines,
                translated_lines=result_lines
            )
            
        except Exception as e:
            return ApplicationResult(
                file_path=file_path,
                policy=ChangePolicy.KEEP_EXISTING,
                applied=False,
                reason="エラーが発生したため適用スキップ",
                original_lines=[],
                translated_lines=[],
                error=str(e)
            )
    
    def _determine_overall_policy(self, policies: List[ChangePolicy]) -> ChangePolicy:
        """複数の操作ポリシーから全体ポリシーを決定"""
        if ChangePolicy.RETRANSLATE in policies:
            return ChangePolicy.RETRANSLATE
        elif ChangePolicy.NEW_TRANSLATION in policies:
            return ChangePolicy.NEW_TRANSLATION
        elif ChangePolicy.DELETE in policies:
            return ChangePolicy.DELETE
        else:
            return ChangePolicy.KEEP_EXISTING
    
    def apply_changes_batch(
        self,
        change_analysis: Dict[str, Any]
    ) -> List[ApplicationResult]:
        """変更分析結果に基づいて一括適用"""
        results = []
        
        file_diffs = change_analysis.get("file_diffs", {})
        
        for file_path, diff_info in file_diffs.items():
            operations = diff_info.get("operations", [])
            if not operations:
                continue
            
            result = self.apply_file_changes(file_path, operations)
            results.append(result)
        
        return results
    
    def generate_application_report(self, results: List[ApplicationResult]) -> str:
        """適用結果のレポートを生成"""
        report_lines = ["📝 変更適用レポート", "=" * 50, ""]
        
        policy_counts = {policy: 0 for policy in ChangePolicy}
        success_count = 0
        error_count = 0
        
        for result in results:
            policy_counts[result.policy] += 1
            if result.applied:
                success_count += 1
            if result.error:
                error_count += 1
        
        # 要約
        report_lines.extend([
            f"処理ファイル数: {len(results)}",
            f"成功: {success_count}, エラー: {error_count}",
            "",
            "ポリシー別集計:",
            f"  既訳維持: {policy_counts[ChangePolicy.KEEP_EXISTING]}",
            f"  新規翻訳: {policy_counts[ChangePolicy.NEW_TRANSLATION]}",
            f"  削除: {policy_counts[ChangePolicy.DELETE]}",
            f"  再翻訳: {policy_counts[ChangePolicy.RETRANSLATE]}",
            "",
            "詳細結果:",
        ])
        
        # 詳細
        for result in results:
            status = "✅" if result.applied else "❌"
            report_lines.extend([
                f"{status} {result.file_path}",
                f"   ポリシー: {result.policy.value}",
                f"   理由: {result.reason}",
            ])
            if result.error:
                report_lines.append(f"   エラー: {result.error}")
            report_lines.append("")
        
        return "\n".join(report_lines)


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Apply upstream changes according to translation policy")
    parser.add_argument(
        "--changes-file",
        required=True,
        help="Changes analysis JSON file from discover_changes.py"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be applied without making changes"
    )
    parser.add_argument(
        "--output-report",
        help="Output file for application report"
    )
    
    args = parser.parse_args()
    
    try:
        # 変更分析ファイルを読み込み
        with open(args.changes_file, 'r', encoding='utf-8') as f:
            change_analysis = json.load(f)
        
        # 変更を適用
        applicator = ChangeApplicator()
        results = applicator.apply_changes_batch(change_analysis)
        
        # レポート生成
        report = applicator.generate_application_report(results)
        
        if args.output_report:
            with open(args.output_report, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ 適用レポートを {args.output_report} に保存しました")
        else:
            print(report)
        
        if args.dry_run:
            print("\n🔍 ドライラン実行：実際のファイル変更は行いませんでした")
        else:
            # 実際のファイル更新を実行
            for result in results:
                if result.applied and not result.error:
                    file_path = Path(result.file_path)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("\n".join(result.translated_lines))
            
            print(f"\n✅ {sum(1 for r in results if r.applied)} ファイルを更新しました")
    
    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()